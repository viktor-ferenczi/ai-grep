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

DEFAULT_HEADER = '#AIGREP_RESULT(index={index!r}, path={path!r}, lineno={lineno!r}, lines={lines!r}, attempt={attempt!r})'
DEFAULT_FAILED = '#AIGREP_FAILED(index={index!r}, path={path!r}, lineno={lineno!r}, lines={lines!r}, attempt={attempt!r})'


class ArgsNamespace(Namespace):
    paths: List[str]

    verbose: int
    config: str
    info: bool
    write: bool

    model: str
    test: bool
    dry: bool
    budget: int
    abort: int

    system: str
    system_file: str
    window: int
    max_tokens: int
    temperature: float
    parallel: int

    validate: str
    regexp: str
    attempts: int
    number: int

    header: str
    failed: str

    encoding: str
    chunk: int
    overlap: int

    recursive: bool
    mimetypes: str
    glob: str
    include: str
    exclude: str
    follow: bool


def create_argument_parser():
    parser = ArgumentParser()
    parser.add_argument('paths', metavar='PATHS', nargs='*', help="Files or folders to process, can contain glob patterns (stdin if none given)")

    g = parser.add_argument_group('Configuration')
    g.add_argument('--verbose', '-v', action='count', default=0, help='Verbose output (-vv for debug)')
    g.add_argument('--config', '-c', default=DEFAULT_CONFIG_PATH, help='Path to the config file')
    g.add_argument('--info', '-i', action='store_true', help='List all configured models and exit')
    g.add_argument('--write', '-W', action='store_true', help='Write the default configuration and exit (does not overwrite)')

    g = parser.add_argument_group('Language model')
    g.add_argument('--model', '-m', help='ID of the model to use (defaults to the first one configured)')
    g.add_argument('--test', '-t', action='store_true', help='Test LLM access and exit')
    g.add_argument('--dry', '-y', action='store_true', help='Dry run (do not use the LLM, provide UNDEFINED results)')
    g.add_argument('--budget', '-B', type=int, help='Maximum tokens to use in total')
    g.add_argument('--abort', '-A', type=int, help='Abort after producing this many outputs')

    g = parser.add_argument_group('Prompt and generation')
    g.add_argument('--system', '-s', default=DEFAULT_SYSTEM, help="System prompt (the default one summarizes the text)")
    g.add_argument('--system-file', '-S', help="Load the system prompt from the file specified")
    g.add_argument('--window', '-w', type=int, help='Context window size (overrides model config)')
    g.add_argument('--max-tokens', '-M', type=int, help='Maximum tokens to generate (overrides calculated default)')
    g.add_argument('--temperature', '-T', type=float, help='Temperature (overrides model config)')
    g.add_argument('--parallel', '-P', type=int, help='Maximum number of parallel generations (overrides model config)')

    g = parser.add_argument_group('Validation and retries')
    g.add_argument('--validate', '-V', help='Validate the output of the LLM: json, yaml, toml, csv (keeps the first valid output)')
    g.add_argument('--regexp', '-e', help='Python regexp to validate LLM output (keeps the first matching output)')
    g.add_argument('--attempts', '-a', type=int, default=1, help='Maximum number of generation attempts to get a valid result (multiplied by --multi)')
    g.add_argument('--number', '-n', type=int, default=1, help='Number of generations per chunk (useful with --regexp)')

    g = parser.add_argument_group('Output formatting')
    g.add_argument('--header', '-H', default=DEFAULT_HEADER, help='Format string of the valid chunk output header')
    g.add_argument('--failed', '-F', default=DEFAULT_FAILED, help='Format string for the invalid chunk output marker')

    g = parser.add_argument_group('Reading and chunking text')
    g.add_argument('--encoding', '-E', default='utf-8', help='Character encoding of all the files')
    g.add_argument('--chunk', '-k', type=int, help='Text chunk size in tokens (default is third of the context size)')
    g.add_argument('--overlap', '-l', type=int, default=0, help='Text chunk overlap in tokens (approximate)')

    g = parser.add_argument_group('Filesystem traversal')
    g.add_argument('--recursive', '-r', action='store_true', help='Recurse into subdirectories')
    g.add_argument('--mimetypes', '-Y', help='Filter files by their mime type (comma separated list)')
    g.add_argument('--glob', '-G', help='Glob pattern to filter the listed files with')
    g.add_argument('--include', '-I', help='Python regexp pattern to filter files by path')
    g.add_argument('--exclude', '-X', help='Python regexp pattern to exclude files by path')
    g.add_argument('--follow', '-L', action='store_true', help='Follow symlinks')

    return parser
