"""data models for meadoc.

arguments:
    `none`

returns:
    `none`
"""

from dataclasses import dataclass
from enum import Enum


class DocstringSection(str, Enum):
    """enum for docstring sections.

    returns:
        `DocstringSection`
            enum member value as string
    """

    ATTRIBUTES = "attributes"
    ARGUMENTS = "arguments"
    METHODS = "methods"
    RETURNS = "returns"
    RAISES = "raises"
    USAGE = "usage"
    UNKNOWN = "unknown"


class ErrorCode(str, Enum):
    """enum for lint error codes.

    returns:
        `ErrorCode`
            enum member value as string
    """

    MISSING = "MDW001"
    OUTDATED = "MDW002"
    MALFORMED = "MDW003"


@dataclass
class DocstringItem:
    """a single item in a docstring section.

    arguments:
        `name: str`
            name of the item
        `type_annotation: str`
            type annotation string
        `description: str`
            description text
        `default_value: str | None = None`
            optional default value
    """

    name: str
    type_annotation: str
    description: str
    default_value: str | None = None


@dataclass
class ParsedDocstring:
    """parsed representation of a meadow docstring.

    attributes:
        `short_description: str`
            short one-line description
        `long_description: str`
            longer detailed description
        `attributes: list[DocstringItem]`
            attribute items
        `arguments: list[DocstringItem]`
            argument items
        `methods: list[DocstringItem]`
            method items
        `returns_type: str | None`
            return type annotation
        `returns_description: str`
            return value description
        `raises: dict[str, str]`
            raised exceptions mapping
        `usage: str | None`
            optional usage example
        `is_malformed: bool`
            whether the docstring is malformed
    """

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
    """a linting issue found during checking.

    arguments:
        `code: ErrorCode`
            error code
        `line: int`
            line number
        `column: int`
            column number
        `message: str`
            error message
    """

    code: ErrorCode
    line: int
    column: int
    message: str


@dataclass
class FunctionSignature:
    """extracted function or method signature.

    arguments:
        `name: str`
            function name
        `parameters: dict[str, str]`
            parameter mapping
        `return_type: str | None`
            return type annotation
        `raises: list[str]`
            list of raised exceptions
    """

    name: str
    parameters: dict[str, str]
    return_type: str | None
    raises: list[str]


@dataclass
class ClassSignature:
    """extracted class signature.

    arguments:
        `name: str`
            class name
        `bases: list[str]`
            base classes
        `attributes: dict[str, str]`
            attribute mapping
        `methods: list[FunctionSignature]`
            list of methods
    """

    name: str
    bases: list[str]
    attributes: dict[str, str]
    methods: list[FunctionSignature]


@dataclass
class ParsedCode:
    """result of parsing a Python file.

    arguments:
        `imports: list[str]`
            list of imports
        `classes: list[ClassSignature]`
            list of classes
        `functions: list[FunctionSignature]`
            list of functions
    """

    imports: list[str]
    classes: list[ClassSignature]
    functions: list[FunctionSignature]
