"""Models for CLI Arguments and pyproject.toml config to be parsed and used by the entry-point."""
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from typing_extensions import TypedDict


if TYPE_CHECKING:
    from pathlib import Path



### CLI Arguments Namespace ###
##################################

class CliArgsNamespace(Protocol):
    """Represents the command-line arguments namespace."""
    plugin_dir: Path | None
    action_scripts: list[str] | None

    # Args always passed in by StreamDeck software
    port: int
    pluginUUID: str  # noqa: N815
    registerEvent: str  # noqa: N815
    info: str  # Actually a string representation of json object


### pyproject.toml Nested Config ###
#######################################

class PyProjectConfigDict(TypedDict):
    """Represents the structure of the pyproject.toml configuration file (or at least for what we care about here)."""
    tool: ToolConfigDict


class ToolConfigDict(TypedDict):
    """Represents the 'tool' section within the pyproject.toml."""
    streamdeck: StreamDeckConfigDict


class StreamDeckConfigDict(TypedDict):
    """Represents the 'streamdeck' configuration section within pyproject.toml."""
    action_scripts: list[str]








