"""Formatter for creating and updating meadow docstrings."""

import ast
from pathlib import Path

from meadow.config import Config
from meadow.models import FunctionSignature
from meadow.parser import parse_file


def format_file(path: Path, config: Config, fix_malformed: bool = False) -> int:
    """Format docstrings in a Python file.

    arguments:
        `path: Path`
            Python file to format
        `config: Config`
            configuration options
        `fix_malformed: bool = False`
            whether to fix malformed docstrings

    returns:
        number of changes made to file
    """
    content = path.read_text()
    parsed = parse_file(path)
    tree = ast.parse(content)

    new_content = _process_tree(tree, parsed, content, config, fix_malformed)

    if new_content != content:
        path.write_text(new_content)
        return 1

    return 0


def _process_tree(
    tree: ast.Module,
    parsed,
    content: str,
    config: Config,
    fix_malformed: bool,
) -> str:
    """Process AST tree and update docstrings."""
    lines = content.split("\n")

    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            existing_docstring = ast.get_docstring(node)

            new_docstring = None

            if isinstance(node, ast.ClassDef):
                class_sig = None
                for cls in parsed.classes:
                    if cls.name == node.name:
                        class_sig = cls
                        break

                if class_sig and (not existing_docstring or fix_malformed):
                    new_docstring = _generate_class_docstring(class_sig, config)

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_sig = None
                for func in parsed.functions:
                    if func.name == node.name:
                        func_sig = func
                        break

                if func_sig and (not existing_docstring or fix_malformed):
                    new_docstring = _generate_function_docstring(func_sig, config)

            if new_docstring:
                lines = _update_docstring(lines, node, new_docstring)

    return "\n".join(lines)


def _update_docstring(lines: list[str], node, new_docstring: str) -> list[str]:
    """Update docstring in lines array.

    arguments:
        `lines: list[str]`
            file content as lines
        `node`
            AST node with docstring
        `new_docstring: str`
            new docstring to insert

    returns:
        updated lines array
    """
    lineno = getattr(node, "lineno", None)
    if lineno is None:
        return lines

    start_line = lineno - 1
    end_line = start_line

    for i in range(start_line, len(lines)):
        if '"""' in lines[i] or "'''" in lines[i]:
            end_line = i
            break

    if start_line >= len(lines):
        return lines

    indentation = len(lines[start_line]) - len(lines[start_line].lstrip())
    indent_str = " " * indentation

    docstring_lines = new_docstring.split("\n")
    formatted_docstring = [indent_str + line for line in docstring_lines]

    lines[start_line : end_line + 1] = formatted_docstring

    return lines


def _generate_class_docstring(class_sig, config: Config) -> str:
    """Generate a meadow docstring for a class.

    arguments:
        `class_sig`
            parsed class signature
        `config: Config`
            configuration options

    returns:
        generated docstring text
    """
    lines = ['"""Short description for ' + class_sig.name + '."', ""]

    if class_sig.attributes:
        lines.append("attributes:")
        for attr_name, attr_type in class_sig.attributes.items():
            type_str = attr_type if attr_type else "Any"
            lines.append(f"    `{attr_name}: {type_str}`")
            lines.append(f"        {config.todoc_message}")
        lines.append("")

    return "\n".join(lines)


def _generate_function_docstring(func_sig: FunctionSignature, config: Config) -> str:
    """Generate a meadow docstring for a function.

    arguments:
        `func_sig: FunctionSignature`
            parsed function signature
        `config: Config`
            configuration options

    returns:
        generated docstring text
    """
    lines = ['"""Short description for ' + func_sig.name + '."', ""]

    if func_sig.parameters:
        lines.append("arguments:")
        for param, param_str in func_sig.parameters.items():
            lines.append(f"    `{param_str}`")
            lines.append(f"        {config.todoc_message}")
        lines.append("")

    if func_sig.return_type:
        lines.append(f"returns: `{func_sig.return_type}`")
        lines.append(f"    {config.todoc_message}")
        lines.append("")

    if func_sig.raises:
        lines.append("raises:")
        for exc in func_sig.raises:
            lines.append(f"    `{exc}`")
            lines.append(f"        {config.todoc_message}")

    return "\n".join(lines)
