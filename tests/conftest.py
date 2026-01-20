"""Test fixtures for meadoc tests."""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing.

    returns:
        temporary directory path that is cleaned up after test
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_py_file(temp_dir):
    """Create a sample Python file for testing.

    arguments:
        `temp_dir`
            temporary directory fixture

    returns:
        path to a sample Python file
    """
    content = '''"""Module docstring."""

def sample_function(x: int, y: int) -> int:
    """A sample function.

    arguments:
        `x: int`
            first argument
        `y: int`
            second argument

    returns:
        sum of x and y
    """
    return x + y


class SampleClass:
    """A sample class."""

    def __init__(self, value: str) -> None:
        """Initialize the class.

        arguments:
            `value: str`
                initial value
        """
        self.value = value

    def get_value(self) -> str:
        """Get the current value.

        returns:
            stored value
        """
        return self.value
'''
    file_path = temp_dir / "sample.py"
    file_path.write_text(content)
    return file_path


@pytest.fixture
def config():
    """Create a test configuration.

    returns:
        test configuration
    """
    from meadow.config import Config

    return Config(
        extend_ignore=[],
        links={},
        todoc_message="TODOC: (meadow)",
    )
