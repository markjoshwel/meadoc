"""configuration handling for meadoc.

arguments:
    `none`

returns:
    `none`
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import tomllib


@dataclass
class Config:
    """configuration for meadoc.

    attributes:
        `extend_ignore: list[str]`
            list of error codes to ignore
        `links: dict[str, str]`
            mapping of external types to documentation urls
        `todoc_message: str`
            placeholder text for undocumented items

    returns:
        `Config`
            config instance
    """

    extend_ignore: list[str] = field(default_factory=list)
    links: dict[str, str] = field(default_factory=dict)
    todoc_message: str = "TODOC: (meadow)"


def parse_extend_ignore(value: Any) -> list[str]:
    """parse extend-ignore configuration value.

    handles string (comma-separated or single), list, or other types.

    arguments:
        `value: Any`
            configuration value to parse

    returns:
        `list[str]`
            list of error code strings
    """
    if isinstance(value, str):
        if "," in value:
            return [code.strip() for code in value.split(",") if code.strip()]
        return [value]
    if isinstance(value, list):
        return value
    return []


def load_pyproject_config(path: Path | None = None) -> Config:
    """load configuration from pyproject.toml.

    reads the `[tool.meadoc]` section from pyproject.toml.

    arguments:
        `path: Path | None = None`
            path to pyproject.toml, defaults to current directory

    returns:
        `Config`
            loaded configuration, or empty config if file not found
    """
    if path is None:
        path = Path.cwd()

    pyproject = path / "pyproject.toml"
    if not pyproject.exists():
        return Config()

    with pyproject.open("rb") as f:
        data = tomllib.load(f)

    meadoc_config = data.get("tool", {}).get("meadoc", {})

    config = Config()

    if "extend-ignore" in meadoc_config:
        config.extend_ignore = parse_extend_ignore(meadoc_config["extend-ignore"])

    if "todoc-message" in meadoc_config:
        config.todoc_message = meadoc_config["todoc-message"]

    return config


def load_meadow_config(path: Path | None = None) -> Config:
    """load configuration from meadow.toml.

    reads configuration from meadow.toml in the specified directory.

    arguments:
        `path: Path | None = None`
            path to meadow.toml, defaults to current directory

    returns:
        `Config`
            loaded configuration, or empty config if file not found
    """
    if path is None:
        path = Path.cwd()

    meadow_toml = path / "meadow.toml"
    if not meadow_toml.exists():
        return Config()

    with meadow_toml.open("rb") as f:
        data = tomllib.load(f)

    config = Config()

    if "extend-ignore" in data:
        config.extend_ignore = parse_extend_ignore(data["extend-ignore"])

    if "links" in data:
        config.links = data["links"]

    if "todoc-message" in data:
        config.todoc_message = data["todoc-message"]

    return config


def merge_configs(
    pyproject_config: Config,
    meadow_config: Config,
    cli_ignore: list[str] | None = None,
    cli_todoc_message: str | None = None,
) -> Config:
    """merge configurations with cli taking precedence.

    merges configurations in priority order:
    1. cli flags (highest)
    2. pyproject.toml
    3. meadow.toml (lowest)

    arguments:
        `pyproject_config: Config`
            configuration from pyproject.toml
        `meadow_config: Config`
            configuration from meadow.toml
        `cli_ignore: list[str] | None = None`
            cli error codes to ignore
        `cli_todoc_message: str | None = None`
            cli todoc message override

    returns:
        `Config`
            merged configuration
    """
    config = Config()

    if pyproject_config.extend_ignore:
        config.extend_ignore = pyproject_config.extend_ignore.copy()

    if meadow_config.extend_ignore:
        config.extend_ignore.extend(
            code for code in meadow_config.extend_ignore if code not in config.extend_ignore
        )

    if meadow_config.links:
        config.links = meadow_config.links.copy()

    if pyproject_config.todoc_message:
        config.todoc_message = pyproject_config.todoc_message

    if meadow_config.todoc_message:
        config.todoc_message = meadow_config.todoc_message

    if cli_ignore:
        for code in cli_ignore:
            if code not in config.extend_ignore:
                config.extend_ignore.append(code)

    if cli_todoc_message:
        config.todoc_message = cli_todoc_message

    return config


def load_config(
    cli_ignore: list[str] | None = None,
    cli_todoc_message: str | None = None,
    path: Path | None = None,
) -> Config:
    """load and merge all configuration sources.

    loads configuration from all sources and merges them with cli taking
    precedence.

    arguments:
        `cli_ignore: list[str] | None = None`
            cli error codes to ignore
        `cli_todoc_message: str | None = None`
            cli todoc message override
        `path: Path | None = None`
            path to config directory, defaults to current directory

    returns:
        `Config`
            merged configuration
    """
    if path is None:
        path = Path.cwd()

    pyproject_config = load_pyproject_config(path)
    meadow_config = load_meadow_config(path)

    return merge_configs(pyproject_config, meadow_config, cli_ignore, cli_todoc_message)


def write_meadow_config(path: Path, config: Config) -> None:
    """write configuration to meadow.toml.

    writes the given config to meadow.toml at the specified path.

    arguments:
        `path: Path`
            path to write meadow.toml
        `config: Config`
            configuration to write

    returns:
        `none`
    """
    toml_lines = []

    toml_lines.append(f"extend-ignore = {config.extend_ignore if config.extend_ignore else []}")
    toml_lines.append("")
    toml_lines.append("[links]")
    toml_lines.append("# discovered third party modules placed here automatically")

    for key, value in config.links.items():
        toml_lines.append(f'"{key}" = "{value}"')

    path.write_text("\n".join(toml_lines))
