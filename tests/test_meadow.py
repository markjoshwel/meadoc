"""Tests for meadoc."""

from pathlib import Path

from meadow.config import parse_extend_ignore, load_config
from meadow.models import ErrorCode
from meadow.traversal import should_ignore
from meadow.parser import parse_file, _parse_docstring
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
    """Test parsing a simple docstring."""
    docstring = "Short description."

    result = _parse_docstring(docstring)

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

    result = _parse_docstring(docstring)

    assert result.short_description == "Short description."
    assert "Longer description here" in result.long_description
    assert len(result.arguments) == 1
    assert result.arguments[0].type_annotation == "x: int"
    assert result.returns_type == "int"


def test_parse_docstring_empty():
    """Test parsing an empty docstring."""
    result = _parse_docstring(None)

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
