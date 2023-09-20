from argparse import ArgumentParser, Namespace
from typing import List

DEFAULT_CONFIG_PATH = '~/.aigrep/config.toml'

DEFAULT_SYSTEM = '''\
You are a document processor. \
Provide a concise summary of the text or code provided.
Be factual, do not make any guesses. \
Stick only to what is written here.' \
Do NOT use any external sources. \
Do NOT judge. \
Do NOT apologise. \
Do NOT refer to your knowledge cut-off date.'''

DEFAULT_FORMAT = '#AIGREP:%s'


class ArgsNamespace(Namespace):
    verbose: int
    config: str
    info: bool
    write: bool
    json: bool
    format: str

    model: str
    test: bool
    dry: bool
    budget: int
    abort: int
    parallel: int

    system: str
    system_file: str
    window: int
    max_tokens: int
    temperature: float

    validate: str
    regexp: str
    attempts: int
    number: int

    encoding: str
    chunk: int
    overlap: int

    recursive: bool
    follow: bool
    exclude: List[str]

    paths: List[str]

    @classmethod
    def from_args(cls, ns: Namespace) -> 'ArgsNamespace':
        return cls(**vars(ns))


def create_argument_parser():
    parser = ArgumentParser()

    g = parser.add_argument_group('Configuration')
    g.add_argument('--verbose', '-v', action='count', default=0, help='Verbose output (-vv for debug)')
    g.add_argument('--config', '-c', default=DEFAULT_CONFIG_PATH, help='Path to the config file')
    g.add_argument('--info', '-i', action='store_true', help='List all configured models and exit')
    g.add_argument('--write', '-W', action='store_true', help='Write the default configuration and exit (does not overwrite)')
    g.add_argument('--json', '-J', action='store_true', help='Produce only machine parseable JSONL output')
    g.add_argument('--format', '-F', default=DEFAULT_FORMAT, help='Python format string for the verbose output lines')

    g = parser.add_argument_group('Language model')
    g.add_argument('--model', '-m', help='ID of the model to use (defaults to the first one configured)')
    g.add_argument('--test', '-t', action='store_true', help='Test LLM access and exit')
    g.add_argument('--dry', '-y', action='store_true', help='Dry run (do not use the LLM, provide UNDEFINED results)')
    g.add_argument('--budget', '-B', type=int, help='Maximum tokens to use in total')
    g.add_argument('--abort', '-A', type=int, help='Abort after producing this many outputs')
    g.add_argument('--parallel', '-P', type=int, help='Maximum number of parallel generations (overrides model config)')

    g = parser.add_argument_group('Prompt and generation')
    g.add_argument('--system', '-s', default=DEFAULT_SYSTEM, help="System prompt (the default one summarizes the text)")
    g.add_argument('--system-file', '-S', help="Load the system prompt from the file specified")
    g.add_argument('--window', '-w', type=int, help='Context window size (overrides model config)')
    g.add_argument('--max-tokens', '-M', type=int, help='Maximum tokens to generate (overrides calculated default)')
    g.add_argument('--temperature', '-T', type=float, help='Temperature (overrides model config)')

    g = parser.add_argument_group('Validation and retries')
    g.add_argument('--validate', '-V', help='Validate the output of the LLM: json, yaml, toml, csv (keeps the first valid output)')
    g.add_argument('--regexp', '-e', help='Python regexp to validate LLM output (keeps the first matching output)')
    g.add_argument('--attempts', '-a', type=int, default=1, help='Maximum number of generation attempts to get a valid result (multiplied by --multi)')
    g.add_argument('--number', '-n', type=int, default=1, help='Number of generations per attempt (useful with --regexp)')

    g = parser.add_argument_group('Reading and chunking text')
    g.add_argument('--encoding', '-E', default='utf-8', help='Character encoding of all the files')
    g.add_argument('--chunk', '-k', type=int, help='Text chunk size in tokens (default is third of the context size)')
    g.add_argument('--overlap', '-l', type=int, default=0, help='Text chunk overlap in tokens (approximate)')

    g = parser.add_argument_group('Filesystem traversal')
    g.add_argument('--recursive', '-r', action='store_true', help='Recursive directory traversal')
    g.add_argument('--follow', '-L', action='store_true', help='Follow symlinks')
    g.add_argument('--exclude', '-X', nargs='*', help='Exclude files matching any of these glob patterns (can be multiple)')

    parser.add_argument('paths', metavar='PATHS', nargs='*', help="Files or folders to process, can contain glob patterns (stdin if none given)")

    return parser
