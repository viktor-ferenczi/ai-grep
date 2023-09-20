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

## Examples

### Finding variables in source code

```sh
aigrep -v -w 500 -V json \
-s "List the name of all variables used in methods and functions. 
Include all member variables, arguments and local variables. 
Write the names as a JSON list. List each variable only once. 
Write the JSON on a single line. 
Do NOT pretty format the JSON. 
Do NOT include expressions or statements, only the variable names. 
Do NOT write anything else. 
Do NOT apoligize. 
Do NOT explain." \ 
*.py
```

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
