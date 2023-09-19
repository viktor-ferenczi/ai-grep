# AIGrep

## Overview

A grep like command line utility to work directly with textual data 
from the command line without having to write specialized code.

- Scans for the files to process
- Reads the files in subsequent chunks
- Feeds the chunks to an LLM using the system prompt provided 
- Prints the generated output in the same order as the original chunks

Chunks are processed in parallel in multiple LLM generations.

## Installation

`pip install aigrep`

## Command line usage

```sh
aigrep -h
```

TBD: Examples

## Configuration

Write out a default configuration file:

```sh
aigrep -w
```

Modify the configuration as needed.

You can also refer to a different configuration file: `-c your/config.toml`

## Library usage

TBD: Refactor the code to be usable as a library.

## Troubleshooting

Use `-v` or `-vv` to output relevant information.
