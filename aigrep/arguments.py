from argparse import ArgumentParser, Namespace
from typing import List, Optional


class ArgsNamespace(Namespace):
    verbose: int
    version: bool

    config: Optional[str]
    default: bool

    recursive: bool
    depth: Optional[int]
    follow: bool
    exclude: List[str]

    model: Optional[str]
    test: bool
    info: bool

    system: Optional[str]
    system_file: Optional[str]
    prompt: Optional[str]
    prompt_file: Optional[str]

    window: Optional[int]
    tokens: Optional[int]
    temperature: Optional[float]
    number: Optional[int]
    attempts: Optional[int]

    converter: Optional[str]
    input_encoding: Optional[str]
    parser: Optional[str]
    filter: Optional[str]

    validator: Optional[str]
    retry: Optional[str]

    output: Optional[str]
    format: Optional[str]
    writer: Optional[str]
    output_encoding: Optional[str]

    budget: Optional[int]
    generations: Optional[int]
    time: Optional[int]

    paths: List[str]

    @classmethod
    def from_args(cls, ns: Namespace) -> 'ArgsNamespace':
        return cls(**vars(ns))


def create_argument_parser():
    parser = ArgumentParser()

    g = parser.add_argument_group('Logging and output')
    g.add_argument('--verbose', '-v', action='count', default=0, help='Verbose output (-vv for debug)')
    g.add_argument('--version', action='store_true', help='Writes out the version number and exit')

    g = parser.add_argument_group('Configuration')
    g.add_argument('--config', '-c', help=f'Path to the configuration file [~/.aigrep/config.toml]')
    g.add_argument('--default', action='store_true', help='Writes the default configuration and exit (does not overwrite)')
    g.add_argument('--tree-sitter', action='store_true', help='Clones the Tree-sitter language parsers and builds the dynamic library')
    g.add_argument('--info', action='store_true', help='Lists all configured models and parsers, then exit')

    g = parser.add_argument_group('Filesystem traversal')
    g.add_argument('--recursive', '-r', action='store_true', help='Recursive directory traversal')
    g.add_argument('--depth', '-d', type=int, help='Maximum recursion depth')
    g.add_argument('--follow', '-L', action='store_true', help='Follow symlinks')
    g.add_argument('--exclude', '-X', nargs='*', help='Exclude files by glob pattern (multiple)')

    g = parser.add_argument_group('Language model')
    g.add_argument('--model', '-m', help='ID of the model to use [first one configured]')
    g.add_argument('--test', action='store_true', help='Tests access to the LLM and exit')

    g = parser.add_argument_group('Prompt')
    g.add_argument('--system', '-s', help="System prompt [concise summarization]")
    g.add_argument('--system-file', '-S', help="System prompt from file")
    g.add_argument('--prompt', '-p', help="Prompt template [input fragment]")
    g.add_argument('--prompt-file', '-P', help="Prompt template from file")

    g = parser.add_argument_group('Generation')
    g.add_argument('--window', '-w', type=int, help='Context window size [model default]')
    g.add_argument('--tokens', '-k', type=int, help='Maximum tokens to generate [remaining window size]')
    g.add_argument('--temperature', '-t', type=float, help='Temperature [model specific]')
    g.add_argument('--number', '-n', type=int, help='Number of generations per attempt [1]')
    g.add_argument('--attempts', '-a', type=int, help='Maximum number of attempts [1]')

    g = parser.add_argument_group('Input processing')
    g.add_argument('--converter', '-C', help='Document to text converter (see Usage)')
    g.add_argument('--input-encoding', '-I', help='Input character encoding [utf-8]')
    g.add_argument('--parser', '-R', help='Input text parser or splitter (see Usage)')
    g.add_argument('--filter', '-f', help='Input fragment filter (see Usage)')

    g = parser.add_argument_group('Output validation')
    g.add_argument('--validator', '-V', help='Output validator (see Usage)')
    g.add_argument('--retry', '-y', help='Retry strategy (see Usage) [immediate]')

    g = parser.add_argument_group('Output formatting')
    g.add_argument('--output', '-o', help='Output selector (see Usage)')
    g.add_argument('--format', '-F', help='Output format (see Usage)')
    g.add_argument('--writer', '-W', help='Output writer (see Usage)')
    g.add_argument('--output-encoding', '-O', help='Output encoding [utf-8]')

    g = parser.add_argument_group('Limits')
    g.add_argument('--budget', '-B', type=int, help='Maximum tokens to generate in total [infinite]')
    g.add_argument('--generations', '-G', type=int, help='Maximum number of generations [infinite]')
    g.add_argument('--time', '-T', type=int, help='Maximum runtime in seconds [infinite]')

    parser.add_argument('paths', metavar='PATHS', nargs='*', help="Files or folders to process, can contain glob patterns (stdin if none given)")

    return parser
