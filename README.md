# AIGrep

_Out of date, unmaintained project. Published it only for reference._

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
-s "List the full name of all companies and their human representatives. 
Write a comma separated list of the names on a single line.
Do NOT write anything else. 
Do NOT apologise. 
Do NOT explain." \ 
*.txt
```

## Configuration

Write out a default configuration file:

```sh
aigrep -w
```

Modify the configuration as needed.

You can also refer to a different configuration file: `-c your/config.toml`

## Backend

### vLLM

To start a [vLLM](https://vllm.readthedocs.io) server on `localhost:8000`:

```sh
python -O -u -m vllm.entrypoints.api_server \
    --host=127.0.0.1 \
    --port=8000 \
    --model=meta-llama/Llama-2-7b \
    --tokenizer=hf-internal-testing/llama-tokenizer \
    --block-size=16 \
    --swap-space=8
```

Change the model and the parameters to match your GPU and specific use case.

To load the model into multiple (N) GPUs:
```
--tensor-parallel-size=N
```

To use a local folder with an already downloaded model:
```
--model=$HOME/models/meta-llama/Llama-2-7b
```

## Library usage

TBD: Refactor the code to be usable as a library.

## Troubleshooting

Use `-v` or `-vv` to output relevant information.
