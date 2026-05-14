"""tests for docstring generation and source updates."""

from pathlib import Path

from meadoc.config import Config
from meadoc.generator import DocstringUpdater


class TestDocstringUpdater:
    """tests for `DocstringUpdater`

    methods:
        `def test_update_file_writes_generated_docstring(self, tmp_path: Path) -> None`
            test missing docstrings are inserted into the source file
        `def test_update_file_writes_multiple_docstrings_in_source_order(
            self, tmp_path: Path
        ) -> None`
            test multiple insertions do not disturb later line positions
        `def test_update_file_replaces_existing_docstring_when_fixing(
            self, tmp_path: Path
        ) -> None`
            test malformed docstrings can be replaced in the source file
    """

    def test_update_file_writes_generated_docstring(self, tmp_path: Path) -> None:
        """test missing docstrings are inserted into the source file

        arguments:
            `tmp_path: Path`
                temporary path fixture

        returns: `none`
            no return value
        """
        source_path = tmp_path / "sample.py"
        source_path.write_text(
            "def add(a: int, b: int) -> int:\n"
            "    return a + b\n",
            encoding="utf-8",
        )

        result = DocstringUpdater(Config.default()).update_file(source_path)

        source = source_path.read_text(encoding="utf-8")
        assert result["generated"] == 1
        assert "    add implementation" in source
        assert "    arguments:" in source
        assert "    returns: `int`" in source
        assert "    return a + b" in source

    def test_update_file_writes_multiple_docstrings_in_source_order(
        self,
        tmp_path: Path,
    ) -> None:
        """test multiple insertions do not disturb later line positions

        arguments:
            `tmp_path: Path`
                temporary path fixture

        returns: `none`
            no return value
        """
        source_path = tmp_path / "sample.py"
        source_path.write_text(
            "def first(value: str) -> str:\n"
            "    return value\n"
            "\n"
            "def second(count: int) -> int:\n"
            "    return count\n",
            encoding="utf-8",
        )

        result = DocstringUpdater(Config.default()).update_file(source_path)

        source = source_path.read_text(encoding="utf-8")
        assert result["generated"] == 2
        assert source.index("first implementation") < source.index("second implementation")
        assert source.count('"""') == 4

    def test_update_file_replaces_existing_docstring_when_fixing(
        self,
        tmp_path: Path,
    ) -> None:
        """test malformed docstrings can be replaced in the source file

        arguments:
            `tmp_path: Path`
                temporary path fixture

        returns: `none`
            no return value
        """
        source_path = tmp_path / "sample.py"
        source_path.write_text(
            "def add(a: int, b: int) -> int:\n"
            "    \"\"\"add two values\"\"\"\n"
            "    return a + b\n",
            encoding="utf-8",
        )

        result = DocstringUpdater(Config.default()).update_file(
            source_path,
            fix_malformed=True,
        )

        source = source_path.read_text(encoding="utf-8")
        assert result["updated"] == 1
        assert "add two values" in source
        assert "    arguments:" in source
        assert "    returns: `int`" in source
