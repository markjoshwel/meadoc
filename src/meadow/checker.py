"""Checker for linting docstrings."""

import ast
from pathlib import Path

from meadow.config import Config
from meadow.models import ErrorCode, FunctionSignature, LintIssue
from meadow.parser import get_docstring_from_node, parse_file, _parse_docstring


def check_file(path: Path, config: Config) -> list[LintIssue]:
    """Check a Python file for docstring issues."""
    issues = []

    try:
        parsed = parse_file(path)
        tree = ast.parse(path.read_text())
    except SyntaxError as e:
        return [
            LintIssue(
                code=ErrorCode.MALFORMED,
                line=e.lineno or 1,
                column=e.offset or 1,
                message=f"Syntax error: {e.msg}",
            )
        ]

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            issues.extend(_check_function(node, parsed, path, config))
        elif isinstance(node, ast.ClassDef):
            issues.extend(_check_class(node, parsed, path, config))

    return sorted(issues, key=lambda i: (i.line, i.column))


def _check_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    parsed,
    path: Path,
    config: Config,
) -> list[LintIssue]:
    """Check a function for docstring issues."""
    issues = []

    docstring = get_docstring_from_node(node)

    if not docstring:
        if ErrorCode.MISSING not in config.extend_ignore:
            issues.append(
                LintIssue(
                    code=ErrorCode.MISSING,
                    line=node.lineno,
                    column=node.col_offset,
                    message=f"function '{node.name}' has no docstring",
                )
            )
        return issues

    parsed_doc = _parse_docstring(docstring)

    if parsed_doc.is_malformed:
        if ErrorCode.MALFORMED not in config.extend_ignore:
            issues.append(
                LintIssue(
                    code=ErrorCode.MALFORMED,
                    line=node.lineno,
                    column=node.col_offset,
                    message=f"function '{node.name}' has a malformed docstring",
                )
            )

    if ErrorCode.OUTDATED not in config.extend_ignore:
        signature = None
        for func in parsed.functions:
            if func.name == node.name:
                signature = func
                break

        if signature:
            param_count = len(signature.parameters)
            doc_param_count = len(parsed_doc.arguments)

            if param_count != doc_param_count:
                issues.append(
                    LintIssue(
                        code=ErrorCode.OUTDATED,
                        line=node.lineno,
                        column=node.col_offset,
                        message=f"function '{node.name}' is outdated: parameter mismatch",
                    )
                )

    return issues


def _check_class(
    node: ast.ClassDef,
    parsed,
    path: Path,
    config: Config,
) -> list[LintIssue]:
    """Check a class for docstring issues."""
    issues = []

    docstring = get_docstring_from_node(node)

    if not docstring:
        if ErrorCode.MISSING not in config.extend_ignore:
            issues.append(
                LintIssue(
                    code=ErrorCode.MISSING,
                    line=node.lineno,
                    column=node.col_offset,
                    message=f"class '{node.name}' has no docstring",
                )
            )
        return issues

    parsed_doc = _parse_docstring(docstring)

    if parsed_doc.is_malformed:
        if ErrorCode.MALFORMED not in config.extend_ignore:
            issues.append(
                LintIssue(
                    code=ErrorCode.MALFORMED,
                    line=node.lineno,
                    column=node.col_offset,
                    message=f"class '{node.name}' has a malformed docstring",
                )
            )

    if ErrorCode.OUTDATED not in config.extend_ignore:
        class_sig = None
        for cls in parsed.classes:
            if cls.name == node.name:
                class_sig = cls
                break

        if class_sig:
            attr_count = len(class_sig.attributes)
            doc_attr_count = len(parsed_doc.attributes)

            if attr_count != doc_attr_count:
                issues.append(
                    LintIssue(
                        code=ErrorCode.OUTDATED,
                        line=node.lineno,
                        column=node.col_offset,
                        message=f"class '{node.name}' is outdated: attribute mismatch",
                    )
                )

    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            issues.extend(_check_function(item, parsed, path, config))

    return issues


def format_issue(issue: LintIssue, file_path: Path) -> str:
    """Format a lint issue for output."""
    return f"{file_path}:{issue.line}:{issue.column}: {issue.code.value}: {issue.message}"
