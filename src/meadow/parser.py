"""
parser for extracting signatures and docstrings using stdlib ast.

extracts function/class signatures from ast nodes, parses existing docstrings
into structured sections, and detects raised exceptions and third-party
references.
"""

import ast
from collections import defaultdict
from pathlib import Path

from meadow.models import (
    ClassSignature,
    DocstringItem,
    DocstringSection,
    FunctionSignature,
    ParsedCode,
    ParsedDocstring,
)


def _type_annotation_to_str(node: ast.AST | None) -> str:
    """
    convert ast type annotation to string

    handles various ast annotation node types and converts them to string
    representation

    arguments:
        `node: ast.AST | None`
            ast node to convert

    returns:
        `str`
            string representation of the type annotation
    """
    if node is None:
        return ""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Subscript):
        return f"{_type_annotation_to_str(node.value)}[{_type_annotation_to_str(node.slice)}]"
    if isinstance(node, ast.Constant):
        return repr(node.value)
    if isinstance(node, ast.BinOp):
        if isinstance(node.op, ast.BitOr):
            return f"{_type_annotation_to_str(node.left)} | {_type_annotation_to_str(node.right)}"
    if isinstance(node, ast.Tuple):
        return ", ".join(_type_annotation_to_str(elt) for elt in node.elts)
    if isinstance(node, ast.Attribute):
        return f"{_type_annotation_to_str(node.value)}.{node.attr}"
    return ""


def _extract_raises(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    """
    extract raised exceptions from function

    walks the ast tree to find `raise` statements and extracts the
    exception types being raised

    arguments:
        `node: ast.FunctionDef | ast.AsyncFunctionDef`
            function or async function node

    returns:
        `list[str]`
            list of exception type names
    """
    raises = []

    for child in ast.walk(node):
        if isinstance(child, ast.Raise):
            exc_type = None
            if isinstance(child.exc, ast.Name):
                exc_type = child.exc.id
            elif isinstance(child.exc, ast.Call):
                if isinstance(child.exc.func, ast.Name):
                    exc_type = child.exc.func.id
                elif isinstance(child.exc.func, ast.Attribute):
                    exc_type = _type_annotation_to_str(child.exc.func)

            if exc_type and exc_type not in raises:
                raises.append(exc_type)

    return raises


def parse_docstring(docstring: str | None) -> ParsedDocstring:
    """
    parse a meadow docstring

    parses a docstring string into structured sections and items. handles the
    meadow docstring format with sections like `arguments:`, `returns:`, etc

    arguments:
        `docstring: str | None`
            docstring text to parse

    returns:
        `ParsedDocstring`
            structured representation of the parsed docstring
    """
    if not docstring:
        return ParsedDocstring(
            short_description="",
            long_description="",
            attributes=[],
            arguments=[],
            methods=[],
            returns_type=None,
            returns_description="",
            raises={},
            usage=None,
            is_malformed=True,
        )

    lines = docstring.split("\n")
    current_section = None
    items_by_section = defaultdict(list)

    short_description = []
    long_description = []
    usage_code = []

    state = "short_desc"

    for line in lines:
        stripped = line.strip()

        if not stripped:
            if state == "short_desc":
                state = "long_desc"
            continue

        if stripped.endswith(":"):
            section_name = stripped[:-1].lower()
            if section_name in [
                "attributes",
                "arguments",
                "methods",
                "returns",
                "raises",
                "usage",
            ]:
                current_section = DocstringSection(section_name)
                state = "section"
                continue

        if state == "short_desc":
            short_description.append(stripped)
        elif state == "long_desc":
            long_description.append(line)
        elif state == "section":
            if current_section == DocstringSection.USAGE:
                usage_code.append(line)
            elif stripped.startswith("`") and "`" in stripped[1:]:
                closing_backtick = stripped.find("`", 1)
                type_part = stripped[1:closing_backtick]
                rest = stripped[closing_backtick + 1 :].strip()
                items_by_section[current_section].append((type_part, rest))
            elif current_section in (
                DocstringSection.ATTRIBUTES,
                DocstringSection.ARGUMENTS,
                DocstringSection.METHODS,
            ):
                if stripped.startswith("`"):
                    closing_backtick = stripped.find("`", 1)
                    if closing_backtick != -1:
                        type_part = stripped[1:closing_backtick]
                        rest = stripped[closing_backtick + 1 :].strip()
                        items_by_section[current_section].append((type_part, rest))
                else:
                    if items_by_section[current_section]:
                        items_by_section[current_section][-1] = (
                            items_by_section[current_section][-1][0],
                            items_by_section[current_section][-1][1] + " " + stripped,
                        )

    parsed = ParsedDocstring(
        short_description=" ".join(short_description),
        long_description="\n".join(long_description).strip(),
        attributes=[],
        arguments=[],
        methods=[],
        returns_type=None,
        returns_description="",
        raises={},
        usage="\n".join(usage_code) if usage_code else None,
        is_malformed=False,
    )

    for type_part, desc in items_by_section.get(DocstringSection.ATTRIBUTES, []):
        parsed.attributes.append(
            DocstringItem(name="", type_annotation=type_part, description=desc)
        )

    for type_part, desc in items_by_section.get(DocstringSection.ARGUMENTS, []):
        parsed.arguments.append(DocstringItem(name="", type_annotation=type_part, description=desc))

    for type_part, desc in items_by_section.get(DocstringSection.METHODS, []):
        parsed.methods.append(DocstringItem(name="", type_annotation=type_part, description=desc))

    if items_by_section.get(DocstringSection.RETURNS):
        returns = items_by_section[DocstringSection.RETURNS][0]
        parsed.returns_type = returns[0].replace("returns: ", "")
        parsed.returns_description = returns[1]

    for type_part, desc in items_by_section.get(DocstringSection.RAISES, []):
        parsed.raises[type_part] = desc

    return parsed


def parse_file(path: Path) -> ParsedCode:
    """
    parse a python file and extract classes, functions, and imports

    walks the ast tree to extract class definitions, function definitions,
    and import statements

    arguments:
        `path: Path`
            path to the python file to parse

    returns:
        `ParsedCode`
            structured representation of the parsed file
    """
    content = path.read_text()
    tree = ast.parse(content)

    imports = []
    classes = []
    functions = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.append(f"{module}.{alias.name}")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            bases = []
            for base in node.bases:
                base_str = _type_annotation_to_str(base)
                if base_str:
                    bases.append(base_str)

            attributes = {}
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    attributes[item.target.id] = _type_annotation_to_str(item.annotation)
                elif isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            attributes[target.id] = ""

            methods = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append(_extract_function_signature(item))

            classes.append(
                ClassSignature(
                    name=node.name,
                    bases=bases,
                    attributes=attributes,
                    methods=methods,
                )
            )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(_extract_function_signature(node))

    return ParsedCode(
        imports=sorted(set(imports)),
        classes=classes,
        functions=functions,
    )


def _extract_function_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> FunctionSignature:
    """
    extract function signature from ast node

    extracts parameter names, types, and defaults, return type, and raised
    exceptions from a function or async function definition

    arguments:
        `node: ast.FunctionDef | ast.AsyncFunctionDef`
            function or async function node

    returns:
        `FunctionSignature`
            structured representation of the function signature
    """
    parameters = {}

    for arg in node.args.posonlyargs:
        param_str = arg.arg
        if arg.annotation:
            param_str += f": {_type_annotation_to_str(arg.annotation)}"
        parameters[arg.arg] = param_str

    for arg in node.args.args:
        param_str = arg.arg
        if arg.annotation:
            param_str += f": {_type_annotation_to_str(arg.annotation)}"
        parameters[arg.arg] = param_str

    for arg in node.args.kwonlyargs:
        param_str = arg.arg
        if arg.annotation:
            param_str += f": {_type_annotation_to_str(arg.annotation)}"
        parameters[arg.arg] = param_str

    if node.args.vararg:
        param_str = f"*{node.args.vararg.arg}"
        if node.args.vararg.annotation:
            param_str += f": {_type_annotation_to_str(node.args.vararg.annotation)}"
        parameters[node.args.vararg.arg] = param_str

    if node.args.kwarg:
        param_str = f"**{node.args.kwarg.arg}"
        if node.args.kwarg.annotation:
            param_str += f": {_type_annotation_to_str(node.args.kwarg.annotation)}"
        parameters[node.args.kwarg.arg] = param_str

    defaults = {
        arg.arg: _type_annotation_to_str(default)
        for arg, default in zip(
            reversed(node.args.args),
            reversed(node.args.defaults),
        )
    }

    for param, default in defaults.items():
        parameters[param] += f" = {default}"

    returns_type = _type_annotation_to_str(node.returns)

    raises = _extract_raises(node)

    return FunctionSignature(
        name=node.name,
        parameters=parameters,
        return_type=returns_type,
        raises=raises,
    )


def get_docstring_from_node(node: ast.AST) -> str | None:
    """
    get docstring from ast node

    returns: docstring for module, class, function, or async function nodes

    arguments:
        `node: ast.AST`
            ast node to get docstring from

    returns:
        `str | None`
            docstring text or none if not found
    """
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
        return ast.get_docstring(node)
    return None


def find_third_party_references(parsed: ParsedCode) -> set[str]:
    """
    find third-party module references from parsed code

    scans class base classes to find references to external modules that are not
    part of the typing module

    arguments:
        `parsed: ParsedCode`
            parsed code structure

    returns:
        `set[str]`
            set of third-party module references
    """
    refs = set()

    for class_sig in parsed.classes:
        for base in class_sig.bases:
            if "." in base and not base.startswith("typing."):
                refs.add(base)

    return refs
