# Design

## Functionality

- File system walker
  - One or more file or folders
  - Glob pattern support
  - Limit recursion depth
  - Optionally follow symlinks
  - Support for exclusion patterns
- For each file type
  - Conversion
    - None
    - PanDoc
    - Custom
  - Text splitter
    - None 
    - Plain text
    - Markdown
    - TreeSitter
    - Custom
    - Overlap
  - For each block type
    - System and prompt template
      - Static text
      - Python string template
      - Custom
    - Validation rules
      - Generation constraint
      - Common format: JSON, YAML, TOML
      - Pattern: RegExp, GLOB
      - Custom
    - Retry rules
      - Maximum count
      - Custom
    - Output formatter
      - Original text
      - LLM output
      - Original, then LLM output
      - Custom
- Model (LLM)
  - Parallel inference (async)

## Options

### Scope

- Path
- File format
- Model

### Overrides

- Filesystem
  - Recursive
  - Follow symlinks
  - Exclusion
- Model
  - ID
  - Backend
  - Configuration
  - Maximum number of parallel generations
  - Number of outputs per prompt
- Content
  - Converter
  - Validator
- Output
  - Validator
  - Formatter 
  - Retry
- Cost
  - Input token (prompt)
  - Output token (generated)
  - Budget (cost limit)
- Input
  - Encoding
- Output
  - Encoding
- Abort
  - Generation count
  - Total cost
  - Warning
  - Error
- Dry run

### Defaults

- Filesystem
  - Process the files listed
  - Walk files directly in the folders listed 
  - Read text from stdin if no paths listed
- Model
  - Use the first configured model in config file
    - If no config file: Connect to vLLM server on 127.0.0.1:8000
- Cost
  - Zero cost, unlimited budget
- Input
  - UTF-8
- Output
    - UTF-8
- Do not abort
- Real run (not a dry run)
