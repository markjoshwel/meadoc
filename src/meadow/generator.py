"""generator for creating markdown api documentation.

arguments:
    `none`

returns:
    `none`
"""

import re
from pathlib import Path

from meadow.config import Config
from meadow.models import FunctionSignature
from meadow.parser import parse_file


def generate_markdown(
    files: list[Path],
    config: Config,
    output: Path | None = None,
    insert_below_header: str | None = None,
    match_pattern: str | None = None,
) -> None:
    """generate markdown api documentation from source files.

    generates a table of contents and structured markdown documentation for
    classes and functions matching the optional pattern.

    arguments:
        `files: list[Path]`
            list of python files to process
        `config: Config`
            configuration options
        `output: Path | None = None`
            output file path, or none for stdout
        `insert_below_header: str | None = None`
            header text to insert content below in output file
        `match_pattern: str | None = None`
            pattern to filter classes/functions by name (glob or regex)

    returns:
        `none`
    """
    markdown_lines = ["## API Reference", "", ""]

    toc_items = []

    for file_path in files:
        parsed = parse_file(file_path)

        for cls in parsed.classes:
            if _matches_pattern(cls.name, match_pattern):
                toc_items.append(f"- [class {cls.name}](#class-{cls.name.lower()})")

        for func in parsed.functions:
            if _matches_pattern(func.name, match_pattern):
                toc_items.append(f"- [function {func.name}](#def-{func.name.lower()})")

    if toc_items:
        markdown_lines.append("- " + "\n- ".join(toc_items))
        markdown_lines.append("")

    for file_path in files:
        parsed = parse_file(file_path)

        for cls in parsed.classes:
            if _matches_pattern(cls.name, match_pattern):
                markdown_lines.extend(_generate_class_markdown(cls, config))

        for func in parsed.functions:
            if _matches_pattern(func.name, match_pattern):
                markdown_lines.extend(_generate_function_markdown(func, config))

    content = "\n".join(markdown_lines)

    if output:
        if output.exists():
            if insert_below_header:
                existing = output.read_text()
                if insert_below_header not in existing:
                    raise FileNotFoundError(f"Header '{insert_below_header}' not found in {output}")

                header_pos = existing.find(insert_below_header)
                insert_pos = header_pos + len(insert_below_header)
                new_content = existing[:insert_pos] + "\n" + content + existing[insert_pos:]
                output.write_text(new_content)
            else:
                existing = output.read_text()
                output.write_text(existing + "\n" + content)
        else:
            output.write_text(content)
    else:
        print(content)


def _matches_pattern(name: str, pattern: str | None) -> bool:
    """check if name matches the given pattern.

    supports glob patterns (default) and regex patterns (if pattern
    starts with `/`).

    arguments:
        `name: str`
            the name to check
        `pattern: str | None = None`
            the pattern (glob or regex)

    returns:
        `bool`
            true if name matches pattern or if no pattern is specified
    """
    if not pattern:
        return True

    if pattern.startswith("/"):
        regex_pattern = pattern[1:]
        return bool(re.match(regex_pattern, name))

    from fnmatch import fnmatch

    return fnmatch(name, pattern)


def _generate_class_markdown(cls, config: Config) -> list[str]:
    """generate markdown for a class.

    creates a markdown section with class description, attributes, and methods.
    applies type links from configuration where available.

    arguments:
        `cls`
            the parsed class signature
        `config: Config`
            configuration options

    returns:
        `list[str]`
            list of markdown lines
    """
    lines = [f"### class {cls.name}", ""]
    lines.append("Short description.")
    lines.append("")

    if cls.attributes:
        lines.append("- attributes:")
        for attr_name, attr_type in cls.attributes.items():
            type_str = attr_type if attr_type else "Any"
            link = _get_type_link(type_str, config)
            lines.append(f"  - {attr_name}: {link if link else f'`{type_str}`'}")
        lines.append("")

    if cls.methods:
        lines.append("- methods:")
        for method in cls.methods:
            link = _get_type_link(f"def {method.name}", config)
            lines.append(f"  - [{method.name}](#def-{method.name.lower()})")

    return lines


def _generate_function_markdown(func: FunctionSignature, config: Config) -> list[str]:
    """generate markdown for a function.

    creates a markdown section with function description, parameters, return
    type, and raised exceptions.

    arguments:
        `func: FunctionSignature`
            the parsed function signature
        `config: Config`
            configuration options

    returns:
        `list[str]`
            list of markdown lines
    """
    lines = [f"### def {func.name}", ""]
    lines.append("Short description.")
    lines.append("")

    if func.parameters:
        lines.append("- arguments:")
        for param, param_str in func.parameters.items():
            type_match = re.search(r":\s*(.+?)(?:\s*=|$)", param_str)
            param_type = type_match.group(1) if type_match else "Any"
            link = _get_type_link(param_type, config)
            lines.append(f"  - {param}: {link if link else f'`{param_type}`'}")
        lines.append("")

    if func.return_type:
        return_link = _get_type_link(func.return_type, config)
        lines.append(f"- returns: {return_link if return_link else f'`{func.return_type}`'}")
        lines.append("")

    if func.raises:
        lines.append("- raises:")
        for exc in func.raises:
            exc_link = _get_type_link(exc, config)
            lines.append(f"  - {exc_link if exc_link else f'`{exc}`'}")
        lines.append("")

    return lines


def _get_type_link(type_str: str, config: Config) -> str | None:
    """get markdown link for a type from config.

    searches the configuration's links dictionary for a matching pattern and
    returns a formatted markdown link if found.

    arguments:
        `type_str: str`
            the type annotation string
        `config: Config`
            configuration options with links

    returns:
        `str | None`
            markdown link if found in config.links, otherwise None
    """
    for pattern, url in config.links.items():
        if pattern in type_str:
            return f"[`{type_str}`]({url})"

    return None
