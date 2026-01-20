"""Configuration handling for meadoc."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import tomllib


@dataclass
class Config:
    """Configuration for meadoc."""

    extend_ignore: list[str] = field(default_factory=list)
    links: dict[str, str] = field(default_factory=dict)
    todoc_message: str = "TODOC: (meadow)"


def parse_extend_ignore(value: Any) -> list[str]:
    """Parse extend-ignore configuration value."""
    if isinstance(value, str):
        if "," in value:
            return [code.strip() for code in value.split(",") if code.strip()]
        return [value]
    if isinstance(value, list):
        return value
    return []


def load_pyproject_config(path: Path | None = None) -> Config:
    """Load configuration from pyproject.toml."""
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
    """Load configuration from meadow.toml."""
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
    """Merge configurations with CLI taking precedence."""
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
    """Load and merge all configuration sources."""
    if path is None:
        path = Path.cwd()

    pyproject_config = load_pyproject_config(path)
    meadow_config = load_meadow_config(path)

    return merge_configs(pyproject_config, meadow_config, cli_ignore, cli_todoc_message)


def write_meadow_config(path: Path, config: Config) -> None:
    """Write configuration to meadow.toml."""
    toml_lines = []

    toml_lines.append(f"extend-ignore = {config.extend_ignore if config.extend_ignore else []}")
    toml_lines.append("")
    toml_lines.append("[links]")
    toml_lines.append("# discovered third party modules placed here automatically")

    for key, value in config.links.items():
        toml_lines.append(f'"{key}" = "{value}"')

    path.write_text("\n".join(toml_lines))
