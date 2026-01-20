"""File traversal for meadoc."""

from fnmatch import fnmatch
from pathlib import Path

FIXED_IGNORE_PATTERNS = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".venv",
    "venv",
    "env",
    "node_modules",
    ".git",
    ".tox",
    "build",
    "dist",
}


def should_ignore(path: Path, ignore_patterns: list[str] | None = None) -> bool:
    """Check if path should be ignored."""
    if ignore_patterns is None:
        ignore_patterns = []

    parts = path.parts

    for part in parts:
        if part in FIXED_IGNORE_PATTERNS:
            return True

    for pattern in ignore_patterns:
        if fnmatch(str(path), pattern):
            return True

    return False


def find_python_files(
    paths: list[Path] | None = None,
    ignore_patterns: list[str] | None = None,
) -> list[Path]:
    """Find Python files in given paths."""
    if paths is None:
        paths = [Path.cwd()]

    python_files = []

    for path in paths:
        if not path.exists():
            continue

        if path.is_file():
            if path.suffix == ".py" and not should_ignore(path, ignore_patterns):
                python_files.append(path)
        elif path.is_dir():
            for item in path.rglob("*.py"):
                if not should_ignore(item, ignore_patterns):
                    python_files.append(item)

    return sorted(set(python_files))


def find_files(
    patterns: list[str],
    paths: list[Path] | None = None,
    ignore_patterns: list[str] | None = None,
) -> list[Path]:
    """Find files matching given patterns."""
    if paths is None:
        paths = [Path.cwd()]

    matched_files = []

    for path in paths:
        if not path.exists():
            continue

        if path.is_file():
            for pattern in patterns:
                if fnmatch(path.name, pattern) and not should_ignore(path, ignore_patterns):
                    matched_files.append(path)
                    break
        elif path.is_dir():
            for item in path.rglob("*"):
                if item.is_file():
                    for pattern in patterns:
                        if fnmatch(item.name, pattern) and not should_ignore(item, ignore_patterns):
                            matched_files.append(item)
                            break

    return sorted(set(matched_files))
