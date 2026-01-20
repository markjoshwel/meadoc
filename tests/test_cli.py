"""Tests for meadoc CLI."""

import subprocess
import tempfile
from pathlib import Path


def test_cli_help():
    """Test running meadoc without arguments shows help."""
    result = subprocess.run(
        ["uv", "run", "meadoc"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "meadoc:" in result.stdout
    assert "Usage:" in result.stdout


def test_cli_format_command(temp_dir):
    """Test format command."""
    file_path = temp_dir / "format_test.py"
    file_path.write_text("def test():\n    pass\n")

    result = subprocess.run(
        ["uv", "run", "meadoc", "format", str(file_path)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0


def test_cli_check_command(temp_dir):
    """Test check command."""
    file_path = temp_dir / "check_test.py"
    file_path.write_text("def test():\n    pass\n")

    result = subprocess.run(
        ["uv", "run", "meadoc", "check", str(file_path)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "MDW001" in result.stdout


def test_cli_toml_command():
    """Test toml command."""
    result = subprocess.run(
        ["uv", "run", "meadoc", "toml"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Configuration" in result.stdout
    assert "extend-ignore" in result.stdout
