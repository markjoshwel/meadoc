# Meadoc Implementation Plan

## Project Overview

Meadoc is a docstring linter and generator for Python projects using the "meadow" docstring format. It validates docstrings, generates them from type hints, and produces markdown API documentation.

## CLI Commands

### `meadoc`
Display description and available commands (help for LLMs and new users).

### `meadoc format [FILE, ...]`
Format/create docstrings in given file(s).

**Options:**
- `--custom-todoc-message MESSAGE` - override placeholder text
- `--fix-malformed` - fix malformed docstrings

**Shared options:**
- `-n, --ignore-no-docstring` - skip MDW001 errors
- `-o, --ignore-outdated` - skip MDW002 errors
- `-m, --ignore-malformed` - skip MDW003 errors
- `--ignore IGNORE` - comma-separated glob patterns to skip

**Behavior:**
- Add missing docstrings with `TODOC: (meadow)` placeholders
- Update existing docstrings preserving descriptions
- Add new sections (attributes/arguments/methods/returns/raises)
- Write third-party references to meadow.toml `[links]`

### `meadoc check [FILE, ...]`
Lint files and output errors/warnings.

**Shared options:** Same as `format`

**Output format:** `file:line:column: CODE: message`

**Error codes:**
- MDW001: Missing docstrings
- MDW002: Outdated docstrings (signature mismatch)
- MDW003: Malformed docstrings (parse errors)

### `meadoc generate [SRC_FILE_OR_DIR, ...]`
Generate markdown API reference from source files/directories.

**Options:**
- `--insert-below-header HEADER_TEXT` - insert into FILE below exact header match
- `--output FILE` - write to file instead of stdout
- `--match MATCH_PATTERN` - filter functions/classes by name
  - Glob pattern by default (e.g., `MyModule*`)
  - Regex if starts with `/` (e.g., `/^MyModule.*/`)

**Behavior:**
- Default output: stdout
- Append to file if `--output` and file exists
- Error if `--insert-below-header` specified but header not found
- Generate table of contents with all items
- Use meadow.toml `[links]` for external references

### `meadoc toml`
Print help/documentation about configuration (meadow.toml and pyproject.toml `[tool.meadoc]`).

## Configuration

### Priority Order
1. CLI flags (highest)
2. pyproject.toml `[tool.meadoc]` section (read-only)
3. meadow.toml file (lowest)

### Configuration Keys

```toml
extend-ignore = ["MDW001", "MDW002"]  # or "MDW001" or "MDW001,MDW002"

[links]
# discovered third party modules placed here automatically
"tomlkit.TOMLDocument" = "https://..."
```

### Config Access by Command

| Command | meadow.toml Access |
|---------|-------------------|
| generate | r- (read-only) |
| format | rw (read-write) |
| check | r- (read-only) |
| toml | -- (help text only) |

## Project Structure

```
meadow/
├── pyproject.toml
├── src/
│   └── meadow/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── parser.py
│       ├── checker.py
│       ├── formatter.py
│       ├── generator.py
│       ├── traversal.py
│       └── models.py
├── tests/
│   ├── conftest.py
│   └── test_meadow.py
└── resources/
    └── apiref.format.md
```

## Core Components

### 1. CLI (`cli.py`)
- Command-line interface using `argparse` or `click`
- Five commands: root help, format, check, generate, toml
- Shared options for format/check commands
- Configuration merging (CLI > pyproject.toml > meadow.toml)

### 2. Config (`config.py`)
- Load configuration from multiple sources
- Parse `extend-ignore` in multiple formats (string, comma-separated, list)
- Load `[links]` section from meadow.toml
- Generate default meadow.toml on first `format` run
- Configuration precedence handling

### 3. Traversal (`traversal.py`)
- File discovery for all commands
- Embedded common ignore patterns (fixed):
  - `__pycache__`, `.pytest_cache`, `.mypy_cache`
  - `.venv`, `venv`, `env`
  - `node_modules`, `.git`
  - `.tox`, `build`, `dist`
  - `*.egg-info`
- Glob pattern matching
- Configurable include/exclude patterns

### 4. Parser (`parser.py`) - uses stdlib `ast`
- Extract function/class signatures
- Parse parameters with types (Python 3.10+ union syntax `A | B`)
- Extract return types
- Parse existing docstrings into sections
- Detect raised exceptions from `Raise` nodes
- Discover third-party module references

### 5. Checker (`checker.py`)
- MDW001: Missing docstrings
- MDW002: Outdated docstrings (signature mismatch)
- MDW003: Malformed docstrings (parse errors)
- Respect ignore flags from CLI and config
- Output format: `file:line:column: CODE: message`

### 6. Formatter (`formatter.py`)
- Preserve existing descriptions
- Add missing sections
- Insert `TODOC: (meadow)` placeholders for new items
- Fix malformed docstrings with `--fix-malformed` flag
- Update return types and exception classes
- Write third-party references to meadow.toml `[links]`

### 7. Generator (`generator.py`)
- Parse meadow docstrings
- Generate markdown with table of contents (all items)
- Create anchor links for internal references
- Apply external links from meadow.toml `[links]`
- Filter by match pattern (glob or regex)
- Insert into existing files under exact header match
- Output to stdout by default, or to file with `--output`

### 8. Models (`models.py`)
- `DocstringSection` enum
- `DocstringItem` dataclass
- `ParsedDocstring` dataclass
- `LintIssue` dataclass (code, line, column, message)
- `FunctionSignature` dataclass
- `Config` dataclass

## Dependencies

- Python 3.13
- stdlib: `ast`, `pathlib`, `tomllib`, `fnmatch`, `glob`, `re`
- Dev: pytest, ruff, mypy, basedpyright

## Meadow Docstring Format

```
<short one line description>

[<more detailed description if needed>]

(attributes OR arguments):
    `python variable declaration syntax`
        description of the attribute

methods:
    `python function signature, including ALL arguments and type hints/return type (if available)`
        description of the method

[
returns: `return type`
    description of the return value
]

[
raises: `singular exception class`
    description of the exception(s) raised
OR
raises:
    `exception class 1`
        description 1
    `exception class 2`
        description 2
    ...
]

[
usage:
    ```py
    ...
    ```
]
```

Sections in square brackets are optional.

## Key Implementation Notes

### Type Syntax
- Generated docstrings use Python 3.10+ union syntax: `A | B`
- External imports referenced in full: `external.ExternalClass`

### Third-Party Links
- `format` command discovers external references and writes to meadow.toml
- `generate` command uses these links for markdown documentation

### Match Pattern Handling
- `--match` applies to both classes and functions
- Default: glob pattern (e.g., `MyModule*`)
- Regex if starts with `/` (e.g., `/^MyModule.*/`)
- Strip `/` prefix for regex compilation

### File Output
- `generate --output FILE`: always appends to existing files
- `generate --output FILE --insert-below-header HEADER`: error if header not found
- `generate` without `--output`: writes to stdout

### Testing Strategy
- Assert-driven tests
- Test configuration precedence
- Test traversal with ignore patterns
- Test glob/regex matching
- Component isolation tests
- CLI integration tests
- Stdout vs file output tests

### Documentation Requirements
- All docstrings must use meadow docstring format
- Write README.md after core implementation is complete

## Git Workflow

**Commit Strategy:**
- Commit and push as you complete each major component
- This helps maintain progress between runs/sessions/compactions
- Use descriptive commit messages for each component

**Example commits:**
- "feat: implement models.py with dataclasses and enums"
- "feat: implement config.py for configuration loading"
- "feat: implement parser.py using stdlib ast"

## Development Commands

```bash
# Run tests
pytest

# Run linting
ruff check src/

# Auto-fix linting issues
ruff check --fix src/

# Type check with mypy
mypy src/

# Type check with basedpyright (optional)
basedpyright src/

# Format code
ruff format src/

# Install dev dependencies
uv add --dev basedpyright ruff mypy pytest

# Install the package in development mode
uv pip install -e .
```
