"""Stream Deck launch arguments parsed with Pydantic Settings."""

from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, DirectoryPath, Field, PrivateAttr, ValidationError, field_validator
from pydantic_settings import CliSettingsSource, SettingsError


class LaunchArguments(BaseModel):
    """Start a Stream Deck plugin with host arguments and development options."""

    # Arguments supplied by the Stream Deck software.
    port: int
    plugin_registration_uuid: str = Field(validation_alias="pluginUUID")
    register_event: str = Field(validation_alias="registerEvent")
    info: dict[str, Any]

    # Development options provided by this SDK.
    plugin_dir: DirectoryPath = Field(default_factory=Path.cwd, validate_default=True)
    action_scripts: Optional[list[str]] = None  # noqa: UP045 - evaluated on Python 3.9
    debug_port: Optional[int] = Field(default=None, validation_alias="debug")  # noqa: UP045

    _source: Optional[CliSettingsSource] = PrivateAttr(default=None)  # noqa: UP045

    @property
    def cli_settings_source(self) -> Optional[CliSettingsSource]:  # noqa: UP045
        """Reuse the parsed CLI source when loading the plugin's settings."""
        return self._source

    @field_validator("info")
    @classmethod
    def validate_plugin_identity(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Ensure launch information supplies the UUID needed for logging."""
        plugin = value.get("plugin")
        if not isinstance(plugin, dict) or not isinstance(plugin.get("uuid"), str):
            message = "info must contain a string at plugin.uuid"
            raise ValueError(message)  # noqa: TRY004 - Pydantic requires ValueError
        return value


_ALIASES = {
    "--port": ("-port", "-p"),
    "--pluginUUID": ("-pluginUUID",),
    "--registerEvent": ("-registerEvent",),
    "--info": ("-info",),
    "--debug": ("-d",),
}


def _add_launch_argument(parser: ArgumentParser, *names: str, **kwargs: Any) -> Any:  # noqa: ANN401
    """Add the host's single-dash long options alongside generated options."""
    aliases = tuple(alias for name in names for alias in _ALIASES.get(name, ()))
    return ArgumentParser.add_argument(parser, *names, *aliases, **kwargs)


def parse_launch_arguments(args: list[str] | None = None) -> LaunchArguments:
    """Parse only CLI input; no environment or configuration sources are used."""
    source = CliSettingsSource(
        LaunchArguments,
        cli_kebab_case=True,
        cli_enforce_required=True,
        cli_hide_none_type=True,
        add_argument_method=_add_launch_argument,
    )
    try:
        source(args=True if args is None else args)
        launch = LaunchArguments.model_validate(source())
    except (ValidationError, SettingsError) as exc:
        source.root_parser.error(str(exc))
    else:
        launch._source = source  # noqa: SLF001 - retain the source alongside its parsed model
        return launch
