"""Command-line interface for meadoc."""

import argparse
import sys
from pathlib import Path

from meadow import __version__
from meadow.checker import check_file, format_issue
from meadow.config import load_config
from meadow.formatter import format_file
from meadow.generator import generate_markdown
from meadow.traversal import find_python_files


def main() -> None:
    """Main entry point for meadoc CLI.

    parses arguments and dispatches to appropriate subcommand.
    """
    parser = argparse.ArgumentParser(
        prog="meadoc",
        description="A docstring linter and generator for Python projects using the meadow docstring format",
    )
    parser.add_argument("--version", action="version", version=f"meadoc {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    _add_format_command(subparsers)
    _add_check_command(subparsers)
    _add_generate_command(subparsers)
    _add_toml_command(subparsers)

    args = parser.parse_args()

    if args.command is None:
        _print_help()
        sys.exit(0)

    match args.command:
        case "format":
            _handle_format(args)
        case "check":
            _handle_check(args)
        case "generate":
            _handle_generate(args)
        case "toml":
            _handle_toml()


def _print_help() -> None:
    """Print help message for LLMs and new users."""
    print("meadoc: A docstring linter and generator for Python projects")
    print("")
    print("Usage:")
    print("  meadoc format [FILE, ...]")
    print("  meadoc check [FILE, ...]")
    print("  meadoc generate [SRC_FILE_OR_DIR, ...]")
    print("  meadoc toml")
    print("")
    print("Run 'meadoc <command> --help' for more information on a specific command.")


def _add_format_command(subparsers) -> None:
    """Add format subcommand."""
    parser = subparsers.add_parser("format", help="Format/create docstrings in given file(s)")
    parser.add_argument("files", nargs="+", type=str, help="Python files to format")
    parser.add_argument(
        "--custom-todoc-message",
        type=str,
        help="Override placeholder text for generated descriptions",
    )
    parser.add_argument(
        "--fix-malformed",
        action="store_true",
        help="Fix malformed docstrings",
    )

    _add_shared_options(parser)


def _add_check_command(subparsers) -> None:
    """Add check subcommand."""
    parser = subparsers.add_parser("check", help="Lint files and output errors/warnings")
    parser.add_argument("files", nargs="+", type=str, help="Python files to check")
    _add_shared_options(parser)


def _add_generate_command(subparsers) -> None:
    """Add generate subcommand."""
    parser = subparsers.add_parser(
        "generate", help="Generate markdown API reference from source files/directories"
    )
    parser.add_argument(
        "src",
        nargs="+",
        type=str,
        help="Source files or directories to process",
    )
    parser.add_argument(
        "--insert-below-header",
        type=str,
        help="Insert output into file below this header",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Write output to file instead of stdout",
    )
    parser.add_argument(
        "--match",
        type=str,
        help="Filter functions/classes by name pattern (glob or regex)",
    )
    _add_shared_options(parser)


def _add_toml_command(subparsers) -> None:
    """Add toml subcommand."""
    subparsers.add_parser("toml", help="Print help about configuration")


def _add_shared_options(parser) -> None:
    """Add shared options to parser."""
    parser.add_argument(
        "-n",
        "--ignore-no-docstring",
        action="store_true",
        help="Ignore missing docstrings (MDW001)",
    )
    parser.add_argument(
        "-o",
        "--ignore-outdated",
        action="store_true",
        help="Ignore outdated docstrings (MDW002)",
    )
    parser.add_argument(
        "-m",
        "--ignore-malformed",
        action="store_true",
        help="Ignore malformed docstrings (MDW003)",
    )
    parser.add_argument(
        "--ignore",
        type=str,
        help="Comma-separated glob patterns to ignore during file traversal",
    )


def _handle_format(args) -> None:
    """Handle format command.

    arguments:
        `args`
            parsed command-line arguments
    """
    config = load_config(
        cli_todoc_message=args.custom_todoc_message,
    )

    ignore_patterns = args.ignore.split(",") if args.ignore else []
    files = find_python_files([Path(f) for f in args.files], ignore_patterns)

    changes = 0
    for file_path in files:
        changes += format_file(file_path, config, args.fix_malformed)

    print(f"Formatted {changes} file(s)")


def _handle_check(args) -> None:
    """Handle check command.

    arguments:
        `args`
            parsed command-line arguments
    """
    config = load_config()

    cli_ignore = []
    if args.ignore_no_docstring:
        cli_ignore.append("MDW001")
    if args.ignore_outdated:
        cli_ignore.append("MDW002")
    if args.ignore_malformed:
        cli_ignore.append("MDW003")

    config = load_config(cli_ignore=cli_ignore)

    ignore_patterns = args.ignore.split(",") if args.ignore else []
    files = find_python_files([Path(f) for f in args.files], ignore_patterns)

    all_issues = []
    for file_path in files:
        issues = check_file(file_path, config)
        for issue in issues:
            all_issues.append(format_issue(issue, file_path))

    for issue_output in all_issues:
        print(issue_output)

    sys.exit(1 if all_issues else 0)


def _handle_generate(args) -> None:
    """Handle generate command.

    arguments:
        `args`
            parsed command-line arguments
    """
    config = load_config()

    cli_ignore = []
    if args.ignore_no_docstring:
        cli_ignore.append("MDW001")
    if args.ignore_outdated:
        cli_ignore.append("MDW002")
    if args.ignore_malformed:
        cli_ignore.append("MDW003")

    config = load_config(cli_ignore=cli_ignore)

    ignore_patterns = args.ignore.split(",") if args.ignore else []
    files = find_python_files([Path(s) for s in args.src], ignore_patterns)

    output_path = Path(args.output) if args.output else None

    generate_markdown(
        files=files,
        config=config,
        output=output_path,
        insert_below_header=args.insert_below_header,
        match_pattern=args.match,
    )


def _handle_toml() -> None:
    """Handle toml command.

    prints help about configuration.
    """
    print("meadoc Configuration")
    print("")
    print("Configuration sources (in priority order):")
    print("  1. CLI flags (highest)")
    print("  2. pyproject.toml [tool.meadoc] section (read-only)")
    print("  3. meadow.toml file (lowest)")
    print("")
    print("Configuration keys:")
    print("")
    print('extend-ignore = ["MDW001", "MDW002"]')
    print('  or "MDW001"')
    print('  or "MDW001,MDW002"')
    print("")
    print("[links]")
    print("  discovered third party modules placed here automatically")
    print('  "tomlkit.TOMLDocument" = "https://..."')
