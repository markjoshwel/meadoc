"""Tests for meadoc."""

from pathlib import Path

from meadow.config import parse_extend_ignore, load_config
from meadow.models import ErrorCode
from meadow.traversal import should_ignore
from meadow.parser import parse_file
from meadow.parser import parse_docstring
from meadow.checker import check_file


def test_parse_extend_ignore_string():
    """Test parsing extend-ignore as a string."""
    result = parse_extend_ignore("MDW001")
    assert result == ["MDW001"]


def test_parse_extend_ignore_comma_separated():
    """Test parsing extend-ignore as comma-separated string."""
    result = parse_extend_ignore("MDW001,MDW002")
    assert result == ["MDW001", "MDW002"]


def test_parse_extend_ignore_list():
    """Test parsing extend-ignore as a list."""
    result = parse_extend_ignore(["MDW001", "MDW002"])
    assert result == ["MDW001", "MDW002"]


def test_parse_extend_ignore_invalid():
    """Test parsing extend-ignore with invalid input."""
    result = parse_extend_ignore(123)
    assert result == []


def test_should_ignore_venv():
    """Test ignoring .venv directory."""
    path = Path(".venv/file.py")
    assert should_ignore(path) is True


def test_should_ignore_pycache():
    """Test ignoring __pycache__ directory."""
    path = Path("src/__pycache__/module.py")
    assert should_ignore(path) is True


def test_should_ignore_regular_file():
    """Test not ignoring regular Python file."""
    path = Path("src/module.py")
    assert should_ignore(path) is False


def test_should_ignore_with_patterns():
    """Test ignoring with custom patterns."""
    path = Path("test_module.py")
    assert should_ignore(path, ["*_test.py", "test_*.py"]) is True


def test_parse_docstring_simple():
    """test parsing a simple docstring."""
    docstring = "Short description."

    result = parse_docstring(docstring)

    assert result.short_description == "Short description."
    assert result.is_malformed is False


def test_parse_docstring_with_sections():
    """Test parsing docstring with sections."""
    docstring = """Short description.

    Longer description here.

    arguments:
        `x: int`
            first argument

    returns:
        `int`
            result
    """

    result = parse_docstring(docstring)

    assert result.short_description == "Short description."
    assert "Longer description here" in result.long_description
    assert len(result.arguments) == 1
    assert result.arguments[0].type_annotation == "x: int"
    assert result.returns_type == "int"


def test_parse_docstring_empty():
    """Test parsing an empty docstring."""
    result = parse_docstring(None)

    assert result.is_malformed is True
    assert result.short_description == ""


def test_parse_file_sample(temp_dir, sample_py_file):
    """Test parsing a sample Python file."""
    parsed = parse_file(sample_py_file)

    assert len(parsed.functions) == 1
    assert parsed.functions[0].name == "sample_function"
    assert len(parsed.classes) == 1
    assert parsed.classes[0].name == "SampleClass"


def test_check_file_missing_docstring(temp_dir, config):
    """Test checking a file with missing docstring."""
    content = "def no_docstring(x: int) -> int:\n    return x\n"
    file_path = temp_dir / "missing.py"
    file_path.write_text(content)

    issues = check_file(file_path, config)

    assert any(issue.code == ErrorCode.MISSING for issue in issues)


def test_check_file_valid_docstring(sample_py_file, config):
    """Test checking a file with valid docstrings."""
    issues = check_file(sample_py_file, config)

    assert len(issues) == 0


def test_load_config_default():
    """Test loading default configuration."""
    config = load_config()

    assert config.extend_ignore == []
    assert config.links == {}
    assert config.todoc_message == "TODOC: (meadow)"


def test_merge_configs():
    """Test merging configurations with CLI precedence."""
    from meadow.config import Config, merge_configs

    pyproject_config = Config(extend_ignore=["MDW001"], todoc_message="from pyproject")
    meadow_config = Config(extend_ignore=["MDW002"], links={"External": "url"})

    merged = merge_configs(
        pyproject_config, meadow_config, cli_ignore=["MDW003"], cli_todoc_message="from cli"
    )

    assert "MDW001" in merged.extend_ignore
    assert "MDW002" in merged.extend_ignore
    assert "MDW003" in merged.extend_ignore
    assert merged.todoc_message == "from cli"
    assert merged.links == {"External": "url"}


def test_find_python_files(temp_dir):
    """Test finding Python files in directory."""
    (temp_dir / "module1.py").write_text("pass")
    (temp_dir / "module2.py").write_text("pass")
    (temp_dir / "test_file.txt").write_text("not python")

    from meadow.traversal import find_python_files

    files = find_python_files([temp_dir])

    assert len(files) == 2
    assert all(f.suffix == ".py" for f in files)


def test_find_python_files_with_ignore(temp_dir):
    """Test finding Python files with ignore patterns."""
    (temp_dir / "good.py").write_text("pass")
    (temp_dir / "bad_test.py").write_text("pass")

    from meadow.traversal import find_python_files

    files = find_python_files([temp_dir], ignore_patterns=["*_test.py"])

    assert len(files) == 1
    assert files[0].name == "good.py"


def test_parse_docstring_with_methods():
    """Test parsing docstring with methods section."""
    docstring = """Sample class.

    methods:
        `def method1(self) -> None: ...`
            description of method1
        `def method2(self, x: int) -> int: ...`
            description of method2
    """

    result = parse_docstring(docstring)

    assert len(result.methods) == 2
    assert "method1" in result.methods[0].type_annotation
    assert "method2" in result.methods[1].type_annotation


def test_parse_docstring_with_raises():
    """Test parsing docstring with raises section."""
    docstring = """Sample function.

    raises:
        `ValueError`
            when value is invalid
        `TypeError`
            when type is wrong
    """

    result = parse_docstring(docstring)

    assert len(result.raises) == 2
    assert "ValueError" in result.raises
    assert "TypeError" in result.raises


def test_parse_file_with_class(temp_dir):
    """Test parsing a file with a class."""
    content = '''
class Example:
    """Example class."""

    value: int

    name: str
'''
    file_path = temp_dir / "class_example.py"
    file_path.write_text(content)

    parsed = parse_file(file_path)

    assert len(parsed.classes) == 1
    assert parsed.classes[0].name == "Example"
    assert "value" in parsed.classes[0].attributes
    assert "name" in parsed.classes[0].attributes


def test_check_file_with_malformed_docstring(temp_dir, config):
    """Test checking file with malformed docstring."""
    content = '''def bad_function():
    """Unclosed docstring.
    return None
'''
    file_path = temp_dir / "bad.py"
    file_path.write_text(content)

    issues = check_file(file_path, config)

    assert any(issue.code == ErrorCode.MALFORMED for issue in issues)


def test_check_file_with_outdated_docstring(temp_dir, config):
    """Test checking file with outdated docstring."""
    content = '''def outdated(x: int, y: int) -> int:
    """Function with outdated docstring.

    arguments:
        `x: int`
            first arg

    returns:
        `int`
        result
    """
    return x + y + z
'''
    file_path = temp_dir / "outdated.py"
    file_path.write_text(content)

    issues = check_file(file_path, config)

    assert any(issue.code == ErrorCode.OUTDATED for issue in issues)


def test_format_issue():
    """Test formatting lint issue."""
    from meadow.models import LintIssue

    issue = LintIssue(code=ErrorCode.MISSING, line=10, column=1, message="test message")

    from meadow.checker import format_issue

    formatted = format_issue(issue, Path("test.py"))

    assert "test.py:10:1: MDW001: test message" in formatted


def test_find_third_party_references(temp_dir):
    """Test finding third-party module references."""
    content = '''
class MyClass(external.ExternalClass):
    """My class with external base."""
    pass
'''
    file_path = temp_dir / "external.py"
    file_path.write_text(content)

    from meadow.parser import find_third_party_references, parse_file

    parsed = parse_file(file_path)
    refs = find_third_party_references(parsed)

    assert "external.ExternalClass" in refs


def test_generate_function_docstring():
    """Test generating function docstring."""
    from meadow.models import FunctionSignature
    from meadow.formatter import _generate_function_docstring
    from meadow.config import Config

    func_sig = FunctionSignature(
        name="example",
        parameters={"x": "x: int", "y": "y: str"},
        return_type="bool",
        raises=["ValueError"],
    )

    config = Config(todoc_message="TODOC: fill this in")

    docstring = _generate_function_docstring(func_sig, config)

    assert "Short description for example." in docstring
    assert "x: int" in docstring
    assert "y: str" in docstring
    assert "returns: `bool`" in docstring
    assert "ValueError" in docstring
    assert "TODOC: fill this in" in docstring


def test_generate_class_docstring():
    """Test generating class docstring."""
    from meadow.formatter import _generate_class_docstring
    from meadow.models import ClassSignature
    from meadow.config import Config

    class_sig = ClassSignature(
        name="Example",
        bases=[],
        attributes={"name": "str", "value": "int"},
        methods=[],
    )

    config = Config(todoc_message="TODOC: fill this in")

    docstring = _generate_class_docstring(class_sig, config)

    assert "Short description for Example." in docstring
    assert "attributes:" in docstring
    assert "name: str" in docstring
    assert "value: int" in docstring
    assert "TODOC: fill this in" in docstring


def test_matches_pattern_glob():
    """Test glob pattern matching."""
    from meadow.generator import _matches_pattern

    assert _matches_pattern("MyClass", "MyClass*") is True
    assert _matches_pattern("MyClass", "Your*") is False


def test_matches_pattern_regex():
    """Test regex pattern matching."""
    from meadow.generator import _matches_pattern

    assert _matches_pattern("MyClass123", "/MyClass\d+") is True
    assert _matches_pattern("MyClassABC", "/MyClass\d+") is False


def test_matches_pattern_none():
    """Test that no pattern matches everything."""
    from meadow.generator import _matches_pattern

    assert _matches_pattern("AnyClass", None) is True


def test_generate_markdown_basic(temp_dir):
    """Test basic markdown generation."""
    content = '''
def sample_func(x: int) -> int:
    """Sample function."""
    return x
'''
    file_path = temp_dir / "sample.py"
    file_path.write_text(content)

    from meadow.generator import _generate_function_markdown
    from meadow.config import Config

    config = Config()

    lines = _generate_function_markdown(
        parse_file(file_path).functions[0],
        config,
    )

    assert any("### def sample_func" in line for line in lines)
    assert any("- arguments:" in line for line in lines)


def test_get_type_link():
    """Test getting type links from config."""
    from meadow.generator import _get_type_link
    from meadow.config import Config

    config = Config(links={"ExternalClass": "https://example.com/ExternalClass"})

    link = _get_type_link("ExternalClass", config)

    assert link is not None
    assert "https://example.com/ExternalClass" in link


def test_get_type_link_not_found():
    """Test getting type link when not in config."""
    from meadow.generator import _get_type_link
    from meadow.config import Config

    config = Config(links={})

    link = _get_type_link("UnknownClass", config)

    assert link is None


def test_type_annotation_to_str_union():
    """Test parsing union type annotation."""
    import ast

    code = "x: int | str"
    tree = ast.parse(code)
    ann = tree.body[0].annotation

    from meadow.parser import _type_annotation_to_str

    result = _type_annotation_to_str(ann)

    assert result == "int | str"


def test_type_annotation_to_str_subscript():
    """Test parsing subscript type annotation."""
    import ast

    code = "x: list[int]"
    tree = ast.parse(code)
    ann = tree.body[0].annotation

    from meadow.parser import _type_annotation_to_str

    result = _type_annotation_to_str(ann)

    assert result == "list[int]"


def test_extract_raises_from_function():
    """Test extracting raised exceptions."""
    import ast

    code = """def func(x: int) -> None:
    if x < 0:
        raise ValueError("negative")
    if x > 100:
        raise TypeError("too large")
"""
    tree = ast.parse(code)
    func_def = tree.body[0]

    from meadow.parser import _extract_raises

    raises = _extract_raises(func_def)

    assert "ValueError" in raises
    assert "TypeError" in raises


def test_parse_async_function(temp_dir):
    """Test parsing async function."""
    content = '''
async def async_func(x: int) -> int:
    """Async function."""
    return x
'''
    file_path = temp_dir / "async_example.py"
    file_path.write_text(content)

    parsed = parse_file(file_path)

    assert len(parsed.functions) == 1
    assert parsed.functions[0].name == "async_func"


def test_parse_class_with_inheritance(temp_dir):
    """Test parsing class with base classes."""
    content = '''
class Child(Parent1, Parent2):
    """Child class."""
    pass
'''
    file_path = temp_dir / "inheritance.py"
    file_path.write_text(content)

    parsed = parse_file(file_path)

    assert len(parsed.classes) == 1
    assert "Parent1" in parsed.classes[0].bases
    assert "Parent2" in parsed.classes[0].bases


def test_write_meadow_config(temp_dir):
    """Test writing meadow.toml configuration."""
    from meadow.config import Config, write_meadow_config

    config = Config(
        extend_ignore=["MDW001"],
        links={"External": "https://example.com"},
        todoc_message="TODOC: (meadow)",
    )

    config_path = temp_dir / "meadow.toml"
    write_meadow_config(config_path, config)

    assert config_path.exists()
    content = config_path.read_text()

    assert "extend-ignore" in content
    assert "[links]" in content
    assert "https://example.com" in content
