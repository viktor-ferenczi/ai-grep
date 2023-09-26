# Usage

## Command line arguments

```shell
usage: aigrep [-h] [--verbose] [--version] [--config CONFIG] [--default]
              [--recursive] [--depth DEPTH] [--follow]
              [--exclude [EXCLUDE ...]] [--model MODEL] [--test] [--info]
              [--system SYSTEM] [--system-file SYSTEM_FILE] [--prompt PROMPT]
              [--prompt-file PROMPT_FILE] [--window WINDOW] [--tokens TOKENS]
              [--temperature TEMPERATURE] [--number NUMBER]
              [--attempts ATTEMPTS] [--converter CONVERTER]
              [--input-encoding INPUT_ENCODING] [--parser PARSER]
              [--filter FILTER] [--validator VALIDATOR] [--retry RETRY]
              [--output OUTPUT] [--format FORMAT] [--writer WRITER]
              [--output-encoding OUTPUT_ENCODING] [--budget BUDGET]
              [--generations GENERATIONS] [--time TIME]
              [PATHS ...]

positional arguments:
  PATHS                 Files or folders to process, can contain glob patterns
                        (stdin if none given)

options:
  -h, --help            show this help message and exit

Logging and output:
  --verbose, -v         Verbose output (-vv for debug)
  --version             Writes out the version number and exit

Configuration:
  --config CONFIG, -c CONFIG
                        Path to the configuration file [~/.aigrep/config.toml]
  --default             Writes the default configuration and exit (does not
                        overwrite)
  --tree-sitter         Clones the Tree-sitter language parsers and builds the
                        dynamic library
  --info                Lists all configured models and parsers, then exit

Filesystem traversal:
  --recursive, -r       Recursive directory traversal
  --depth DEPTH, -d DEPTH
                        Maximum recursion depth
  --follow, -L          Follow symlinks
  --exclude [EXCLUDE ...], -X [EXCLUDE ...]
                        Exclude files by glob pattern (multiple)

Language model:
  --model MODEL, -m MODEL
                        ID of the model to use [first one configured]
  --test                Tests access to the LLM and exit

Prompt:
  --system SYSTEM, -s SYSTEM
                        System prompt [concise summarization]
  --system-file SYSTEM_FILE, -S SYSTEM_FILE
                        System prompt from file
  --prompt PROMPT, -p PROMPT
                        Prompt template [input fragment]
  --prompt-file PROMPT_FILE, -P PROMPT_FILE
                        Prompt template from file

Generation:
  --window WINDOW, -w WINDOW
                        Context window size [model default]
  --tokens TOKENS, -k TOKENS
                        Maximum tokens to generate [remaining window size]
  --temperature TEMPERATURE, -t TEMPERATURE
                        Temperature [model specific]
  --number NUMBER, -n NUMBER
                        Number of generations per attempt [1]
  --attempts ATTEMPTS, -a ATTEMPTS
                        Maximum number of attempts [1]

Input processing:
  --converter CONVERTER, -C CONVERTER
                        Document to text converter (see Usage)
  --input-encoding INPUT_ENCODING, -I INPUT_ENCODING
                        Input character encoding [utf-8]
  --parser PARSER, -R PARSER
                        Input text parser or splitter (see Usage)
  --filter FILTER, -f FILTER
                        Input fragment filter (see Usage)

Validation:
  --validator VALIDATOR, -V VALIDATOR
                        Output validator (see Usage)
  --retry RETRY, -y RETRY
                        Retry strategy (see Usage) [immediate]

Output formatting:
  --output OUTPUT, -o OUTPUT
                        Output selector (see Usage)
  --format FORMAT, -F FORMAT
                        Output format (see Usage)
  --writer WRITER, -W WRITER
                        Output writer (see Usage)
  --output-encoding OUTPUT_ENCODING, -O OUTPUT_ENCODING
                        Output encoding [utf-8]

Limits:
  --budget BUDGET, -B BUDGET
                        Maximum tokens to generate in total [infinite]
  --generations GENERATIONS, -G GENERATIONS
                        Maximum number of generations [infinite]
  --time TIME, -T TIME  Maximum runtime in seconds [infinite]
```

* (see Usage) => See below

## Operations

On parameters accepting operations specify one of:

- `built-in-option-1`
- `built-in-option-2`
- `sh:shell command`
- `py:python class or function`

Unspecified operations are automatically selected based on the
file type or skipped with default action wherever applicable.

### Shell commands

Shell commands receive their input via `$1` (first argument).

Boolean output is expected to be returned via the exit code:

- `0` is `true`
- `1` is `false`
- any other exit code is an error.

Text output is expected to be written to stdout, in which case
any non-zero exit code is an error.

Shell commands are executed in the same temporary folder where
the temporary files are, so generate any output file directly
there. Temporary files are cleaned up automatically.

### Python code

Python classes or functions are imported, therefore they need
to be fully qualified:

- `package.module.function`
- `package.module.Class`

#### Segment

Python code receiving segments use the following dataclass:

```python
from dataclasses import dataclass


@dataclass
class Segment:
    path: str  # Path of the original document
    attempt: int  # Attempt number when the generation succeeded (useful for diagnostics)
    depth: int  # Depth provided by the parser (useful for code and structured text)
    category: str  # Category of the segment (useful for code and structured text)
    index: int  # Index of the generation (non-zero only if --number is more than 1)
    text: str  # Text of the segment
    token_count: int  # Input token count
```

#### Output

Generated output is represented by the following dataclass:

```python
from dataclasses import dataclass


@dataclass
class Output:
    text: str  # Generated tex
    token_count: int  # Output token count
```

## Input converter

Converts an input file to text.

Shell command parameters:
- `$1`: Path of the input document file

```shell
--converter 'sh:pandoc -f pdf -t plain --output=- $1'
--converter 'py:mypackage.mymodule.converter_function'
```

```python
def converter_function(path: str) -> str:
    ...
```

## Text parser

Parses or splits the input text into segments.
Each segment should contain information which
logically belongs together. The segment size
should not exceed max_tokens.

Shell command parameters:
- `$1`: Path of text file
- `$2`: `max_tokens`

Shell command output must be a list of filenames, one on each line.
The shell command is executed in a temporary folder, therefore
create the split files directly in there.

```shell
--parser 'sh:split -l 100 $1 segment-; ls -1 | grep segment-'
--parser 'py:aigrep.splitters.MarkdownSplitter'
--parser 'py:aigrep.parsers.CSharpParser'
```

Many text splitters and parsers are provided. Programming language parsers
are based on [Tree-sitter](https://tree-sitter.github.io), which requires
Git and Rust to be used. The Tree-sitter repositories are cloned under
`~/.cache/tree-sitter` and built as a single dynamic library file. Run 
`aigrep --tree-sitter` once before using the programming language parsers.

Custom parsers must adhere to this interface:

```python
from typing import Callable, Iterable


class Parser:
    def __init__(self, count_tokens: Callable[[str], int]):
        self.count_tokens: Callable[[str], int] = count_tokens

    def parser(self, path: str, input: str, max_tokens: int) -> Iterable[Segment]:
        ...
```

## Segment filter

Determines which segments to keep for processing.

Shell command parameters:
- `$1`: input text path
- `$2`: attempt
- `$3`: depth
- `$4`: category
- `$5`: index
- `$6`: input token count

```shell
--filter 'sh:grep "StringToLookFor" $1'
--filter 'py:mypackage.mymodule.filter_segment'
```

```python
def filter_segment(segment: Segment) -> bool:
    ...
``` 

## Output validator

Validates the generated text.

Shell command parameters:
- `$1`: input text path
- `$2`: attempt
- `$3`: depth
- `$4`: category
- `$5`: index
- `$6`: input token count
- `$7`: output text path
- `$8`: output token count

```shell
--validator 'json'
--validator 'yaml'
--validator 'toml'
--validator 'sh:python -m py_compile $7'
--validator 'py:mypackage.mymodule.is_valid_output'
```

The `json`, `yaml` and `toml` validators automatically detect
a code block in the output and consider only its contents if
it exists, otherwise the whole output is validated.

```python
def is_valid_output(segment: Segment, output: str) -> bool:
    ...
```

## Retry strategy

Retry immediately or using a queue via a round-robin manner.

```shell
--retry immediate
--retry queue
```

## Output selector

Selects which valid generation(s) to output.

The shell command is called for each output one by one.

Shell command parameters:
- `$1`: input text path
- `$2`: attempt
- `$3`: depth
- `$4`: category
- `$5`: index
- `$6`: input token count
- `$7`: output text path
- `$8`: output token count

```shell
--output 'sh:grep "StringToLookFor" $7'
--output 'py:mypackage.mymodule.select_output'
```

```python
from typing import List


def select_output(segment: Segment, valid_outputs: List[str]) -> List[str]:
    ...
```

## Output formatter

The shell command is called for each output one by one.

Shell command parameters:
- `$1`: input text path
- `$2`: attempt
- `$3`: depth
- `$4`: category
- `$5`: index
- `$6`: input token count
- `$7`: output text path
- `$8`: output token count

```shell
--format 'sh:jq . $7'
--format 'py:mypackage.mymodule.format_output'
```

```python
from typing import List


def select_output(segment: Segment, valid_outputs: List[str]) -> List[str]:
    ...
```

### Output writer

```shell
--writer 'sh:cat $1 >>/path/to/my/output.txt'
--writer 'py:mypackage.mymodule.write_output'
```

```python
def write_output(segment: Segment, output: str):
    with open(f'{segment.path}.summary-{segment.index}.txt', 'wt') as f:
        f.write(output)
```
