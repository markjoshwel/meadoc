"""Data models for meadoc."""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class DocstringSection(str, Enum):
    """Enum for docstring sections."""

    ATTRIBUTES = "attributes"
    ARGUMENTS = "arguments"
    METHODS = "methods"
    RETURNS = "returns"
    RAISES = "raises"
    USAGE = "usage"
    UNKNOWN = "unknown"


class ErrorCode(str, Enum):
    """Enum for lint error codes."""

    MISSING = "MDW001"
    OUTDATED = "MDW002"
    MALFORMED = "MDW003"


@dataclass
class DocstringItem:
    """A single item in a docstring section."""

    name: str
    type_annotation: str
    description: str
    default_value: str | None = None


@dataclass
class ParsedDocstring:
    """Parsed representation of a meadow docstring."""

    short_description: str
    long_description: str
    attributes: list[DocstringItem]
    arguments: list[DocstringItem]
    methods: list[DocstringItem]
    returns_type: str | None
    returns_description: str
    raises: dict[str, str]
    usage: str | None
    is_malformed: bool


@dataclass
class LintIssue:
    """A linting issue found during checking."""

    code: ErrorCode
    line: int
    column: int
    message: str


@dataclass
class FunctionSignature:
    """Extracted function or method signature."""

    name: str
    parameters: dict[str, str]
    return_type: str | None
    raises: list[str]


@dataclass
class ClassSignature:
    """Extracted class signature."""

    name: str
    bases: list[str]
    attributes: dict[str, str]
    methods: list[FunctionSignature]


@dataclass
class ParsedCode:
    """Result of parsing a Python file."""

    imports: list[str]
    classes: list[ClassSignature]
    functions: list[FunctionSignature]
