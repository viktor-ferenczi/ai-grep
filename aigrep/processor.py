import asyncio
import glob
import json
import mimetypes
import os.path
import re
import sys
from asyncio import Queue, Task, Semaphore
from dataclasses import dataclass, asdict
from typing import List, TextIO, AsyncIterable, Tuple, Optional, Iterable, Set

import toml
import yaml
from vllm_client.sampling_params import SamplingParams

from aigrep.config import Config
from aigrep.model import Model
from aigrep.utils import count_tokens, log, extract_code_block
from arguments import ArgsNamespace


@dataclass
class Chunk:
    index: int
    path: str
    lineno: int
    lines: int
    input: str
    output: str = ''
    attempt: int = 0
    successful: bool = False


class Processor:

    def __init__(self, args: ArgsNamespace, config: Config, model: Model):
        super().__init__()
        self.args: ArgsNamespace = args
        self.config: Config = config
        self.model: Model = model

        self.chunk_size: int = self.args.chunk or (self.model.cfg.context // 3)
        self.chunk_overlap: int = self.args.overlap

        system: str = self.args.system
        if self.args.system_file:
            with open(self.args.system_file, 'rt', encoding='utf-8') as f:
                system: str = f.read().strip()

        prompt_tokens: int = count_tokens(self.model.cfg.prompt_template.format(system=system, instruction=''))
        assert 0 < self.chunk_size <= self.model.cfg.context - prompt_tokens, f'Invalid chunk size: {self.chunk_size}'
        assert 0 <= self.chunk_overlap < self.chunk_size, f'Invalid chunk overlap: {self.chunk_overlap}'

        max_tokens: int = self.model.cfg.context - prompt_tokens - self.chunk_size if self.args.max_tokens is None else self.args.max_tokens
        assert max_tokens > 0, f'Invalid max tokens: {max_tokens}'

        self.params: SamplingParams = SamplingParams(
            n=self.args.number,
            max_tokens=max_tokens,
            **self.model.cfg.sampling_params_dict)

        if self.args.temperature is not None:
            self.params.temperature = self.args.temperature

        self.mimetypes: Optional[Set[str]] = set(self.args.mimetypes.split(',')) if self.args.mimetypes else None
        self.rx_include: re.Pattern = re.compile(self.args.include) if self.args.include else None
        self.rx_exclude: re.Pattern = re.compile(self.args.exclude) if self.args.exclude else None
        self.rx_regexp: re.Pattern = re.compile(self.args.regexp) if self.args.regexp else None

        self.parallel: int = max(1, self.args.parallel or self.model.cfg.parallel)
        self.input_queue: Queue[Chunk] = Queue(self.parallel)
        self.output_queue: Queue[Chunk] = Queue(self.parallel)
        self.semaphore = Semaphore(self.parallel)
        self.next_chunk_index = 0
        self.generation_count = 0
        self.failure_count = 0
        self.finished_reading = False
        self.abort: bool = False
        self.tasks: List[Task] = []

        self.cost: int = 0
        self.budget: Optional[int] = self.args.budget

        self.dry = self.args.dry
        self.verbose = self.args.verbose > 0
        self.debug = self.args.verbose > 1

    def log_verbose(self, event: str, **kws):
        if self.verbose:
            log(event, **kws)

    def log_debug(self, event: str, **kws):
        if self.debug:
            log(event, **kws)

    def check_finished(self, results):
        if self.finished_reading and not self.generation_count and not results and self.input_queue.empty() and self.output_queue.empty():
            self.log_debug('FINISHED')
            self.stop()

    def stop(self):
        self.abort = True
        for task in self.tasks:
            task.cancel()

    async def process(self) -> bool:
        self.log_debug('STARTED')

        paths: Set[str] = {
            os.path.normpath(path).replace('\\', '/')
            for path in self.find_files()
            if self.is_valid_file(path)
        }

        if not paths:
            self.log_verbose('NO_FILES_FOUND')
            return False

        sorted_paths = sorted(paths)
        del paths

        self.log_debug('FILES_FOUND', count=len(sorted_paths), paths=sorted_paths)

        assert not self.tasks

        self.tasks.extend([
            asyncio.create_task(self.reader(sorted_paths)),
            asyncio.create_task(self.printer()),
        ])

        self.tasks.extend(
            asyncio.create_task(self.generator())
            for _ in range(self.parallel)
        )

        await asyncio.wait(self.tasks, return_when=asyncio.ALL_COMPLETED)

        self.tasks.clear()

        if self.failure_count:
            self.log_verbose('FAILED_CHUNKS', count=self.failure_count)

        return self.failure_count == 0

    async def reader(self, paths: List[str]) -> None:
        for path in paths:
            self.log_debug('READER_FILE', path=path)

            async for chunk in self.read_path(path):
                if self.abort:
                    return
                self.log_debug('READER_CHUNK', index=chunk.index, path=chunk.path, lineno=chunk.lineno, lines=chunk.lines)
                await self.input_queue.put(chunk)
                if self.abort:
                    return

        self.finished_reading = True

    async def printer(self):
        # Chunk reordering buffer
        results: List[Optional[Chunk]] = []
        first_index: int = 0

        # Total number of outputs printed
        print_count: int = 0
        abort_at: Optional[int] = self.args.abort

        while not self.abort:
            chunk: Chunk = await self.output_queue.get()
            assert chunk.index >= first_index

            self.log_debug('PRINTER_CHUNK', index=chunk.index, path=chunk.path, lineno=chunk.lineno, lines=chunk.lines, attempt=chunk.attempt)

            # Reserve slots
            while chunk.index - first_index >= len(results):
                results.append(None)

            # Store
            results[chunk.index - first_index] = chunk

            while not self.abort and results and results[0]:
                result = results.pop(0)
                first_index += 1

                if result.successful:
                    if self.verbose:
                        print(self.args.header.format(**asdict(result)))
                    print(result.output)
                else:
                    if self.verbose:
                        print(self.args.failed.format(**asdict(result)))

                print_count += 1
                if abort_at is not None and print_count >= abort_at:
                    self.stop()

            self.check_finished(results)

    async def generator(self):
        while not self.abort:
            chunk: Chunk = await self.input_queue.get()
            chunk.attempt += 1

            self.generation_count += 1
            try:
                self.log_debug('GENERATOR_ATTEMPT', index=chunk.index, path=chunk.path, lineno=chunk.lineno, lines=chunk.lines, attempt=chunk.attempt)

                async with self.semaphore:
                    if self.dry:
                        outputs = [('DRY RUN RESULT', 10) for _ in range(self.params.n)]
                    else:
                        outputs = await self.model.generate(self.args.system, chunk.input, self.params)

                output = self.select_valid_output(outputs)
                if output is None:
                    retry = chunk.attempt < self.args.attempts
                    if retry:
                        self.log_debug('GENERATOR_RETRY', index=chunk.index, path=chunk.path, lineno=chunk.lineno, lines=chunk.lines, attempt=chunk.attempt)
                        await self.input_queue.put(chunk)
                    else:
                        self.log_debug('GENERATOR_FAILED', index=chunk.index, path=chunk.path, lineno=chunk.lineno, lines=chunk.lines, attempt=chunk.attempt)
                        await self.output_queue.put(chunk)
                        self.failure_count += 1
                    continue

                text, cost = output
                chunk.output = text
                chunk.successful = True

                self.log_debug('GENERATOR_FINISHED', index=chunk.index, path=chunk.path, lineno=chunk.lineno, lines=chunk.lines, attempt=chunk.attempt, cost=cost)
                await self.output_queue.put(chunk)

                self.cost += cost
                if self.budget and self.cost > self.budget:
                    self.stop()
                    self.log_verbose('OVER_BUDGET', cost=self.cost, budget=self.budget)
            finally:
                self.generation_count -= 1

    def select_valid_output(self, outputs: List[Tuple[str, int]]) -> Optional[Tuple[str, int]]:
        for output in outputs:
            text, cost = output
            text, valid = self.verify_fix_generation(text)
            if valid:
                return text, cost
        return None

    def verify_fix_generation(self, text: str) -> Tuple[str, bool]:
        original = text

        if self.rx_regexp is not None:
            if self.rx_regexp.match(text) is None:
                self.log_debug('SKIP_NOT_MATCHING_REGEXP')
                if self.debug:
                    print(text)
                return text, False

        validate = self.args.validate
        if validate is None:
            pass
        elif validate == 'json':
            normalized = extract_code_block(text, 'json').strip()
            try:
                json.loads(normalized)
            except json.JSONDecodeError:
                self.log_debug('SKIP_INVALID_JSON')
                if self.debug:
                    print(text)
                return original, False
            return normalized, True
        elif validate == 'yaml':
            normalized = extract_code_block(text, 'yaml').strip('\n')
            try:
                yaml.safe_load(normalized)
            except yaml.YAMLError:
                self.log_debug('SKIP_INVALID_YAML')
                if self.debug:
                    print(text)
                return original, False
            return normalized, True
        elif validate == 'toml':
            normalized = extract_code_block(text, 'toml').strip('\n')
            try:
                toml.loads(normalized)
            except toml.TomlDecodeError:
                self.log_debug('SKIP_INVALID_TOML')
                if self.debug:
                    print(text)
                return original, False
            return normalized, True
        else:
            print(f'ERROR: Invalid validation mode: {validate}', file=sys.stderr)
            sys.exit(1)

        return original, True

    def find_files(self) -> Iterable[str]:
        paths = self.args.paths

        if self.args.glob:
            yield from glob.glob(self.args.glob or '**', root_dir=os.getcwd(), recursive=self.args.recursive)
        elif not paths:
            paths = ['.']

        for path in paths:
            if os.path.isdir(path):
                yield from glob.glob(os.path.join(path, '**'), root_dir=path, recursive=self.args.recursive)
            else:
                yield from glob.glob(path, root_dir=os.path.dirname(path), recursive=self.args.recursive)

    def is_valid_file(self, path: str) -> bool:
        if not os.path.isfile(path) and not os.path.islink(path):
            self.log_debug('SKIP_NOT_A_FILE', path=path)
            return False

        if self.mimetypes is not None:
            if mimetypes.guess_type(path) not in self.mimetypes:
                self.log_debug('SKIP_NOT_IN_MIMETYPES', path=path)
                return False

        if self.rx_include is not None:
            if self.rx_include.match(path) is None:
                self.log_debug('SKIP_NOT_IN_INCLUDE', path=path)
                return False

        if self.rx_exclude is not None:
            if self.rx_exclude.match(path) is not None:
                self.log_debug('SKIP_IN_EXCLUDE', path=path)
                return False

        if sys.platform != 'win32':
            if not os.access(path, os.R_OK, follow_symlinks=self.args.follow):
                self.log_debug('SKIP_NO_ACCESS', path=path)
                return False

        return True

    async def read_path(self, path: str) -> AsyncIterable[Chunk]:
        self.log_debug('READING_FILE', path=path)

        if path == '-':
            async for lineno, text in self.read_file(sys.stdin):
                yield Chunk(self.next_chunk_index, '-', lineno, text.count('\n'), text)
                self.next_chunk_index += 1
            return

        with open(path, 'rt', encoding=self.args.encoding) as f:
            try:
                async for lineno, text in self.read_file(f):
                    yield Chunk(self.next_chunk_index, path, lineno, text.count('\n'), text)
                    self.next_chunk_index += 1
            except UnicodeDecodeError:
                self.log_verbose('FAILED_TO_DECODE', path=path, encoding=self.args.encoding)

    async def read_file(self, f: TextIO) -> AsyncIterable[Tuple[int, str]]:
        lines = []
        tokens = 0
        lineno = 1

        for line in f:

            line_tokens = count_tokens(line)
            if tokens + line_tokens >= self.chunk_size:

                # Trim lines longer than chunk size
                if not tokens and line_tokens:
                    line = line[:len(line) * self.chunk_size // line_tokens]
                    line_tokens = count_tokens(line)
                    while line and line_tokens and line_tokens > self.chunk_size:
                        line = line[:len(line) * 95 // 100]
                        line_tokens = count_tokens(line)

                text = ''.join(lines)
                if text.strip():
                    yield lineno, text

                if self.chunk_overlap:
                    while lines and tokens > self.chunk_overlap:
                        tokens -= count_tokens(lines[0])
                        lineno += lines[0].count('\n')
                        del lines[0]
                else:
                    lines.clear()
                    tokens = 0
                    lineno += text.count('\n')

            lines.append(line)
            tokens += line_tokens

        if lines:
            text = ''.join(lines)
            if text.strip():
                yield lineno, text
