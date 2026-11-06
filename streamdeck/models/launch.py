"""Stream Deck launch arguments parsed with Pydantic Settings."""

from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
from typing import Any

from pydantic import AliasPath, BaseModel, DirectoryPath, Field
from pydantic_settings import (
    BaseSettings,
    CliSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


class RegistrationInfo(BaseModel):
    """Extract the plugin identity used by this SDK from launch information."""

    plugin_uuid: str = Field(validation_alias=AliasPath("plugin", "uuid"))


class LaunchArguments(BaseSettings):
    """Start a Stream Deck plugin with host arguments and development options."""

    model_config = SettingsConfigDict(
        cli_parse_args=True,
        cli_kebab_case=True,
        cli_enforce_required=True,
        cli_hide_none_type=True,
    )

    # Arguments supplied by the Stream Deck software.
    port: int
    """Port of the WebSocket server provided by Stream Deck."""

    plugin_registration_uuid: str = Field(validation_alias="pluginUUID")
    """Per-launch registration identifier supplied as -pluginUUID, distinct from the manifest plugin UUID."""

    register_event: str = Field(validation_alias="registerEvent")
    """Registration event name supplied as -registerEvent, normally registerPlugin."""

    info: RegistrationInfo
    """Launch information supplied as JSON through -info, modeled to extract plugin.uuid."""

    # Development options provided by this SDK.
    plugin_dir: DirectoryPath = Field(default_factory=Path.cwd, validate_default=True)
    """Existing directory added to the module import path; defaults to the working directory and does not select the TOML file."""

    action_scripts: list[str] | None = None
    """Importable action module names supplied through repeated --action-scripts options, replacing the TOML list when nonempty."""

    event_listener_modules: list[str] | None = None
    """Importable listener module names supplied through repeated --event-listener options (also --event-listener-modules), replacing the TOML list."""

    debug_port: int | None = Field(default=None, validation_alias="debug")
    """Debugger port supplied through --debug or -d; a nonzero value enables attachment and waits for a debugger."""

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        **_sources: PydanticBaseSettingsSource,
    ) -> tuple[CliSettingsSource]:
        """Parse only CLI arguments, preserving the host-specific option aliases."""
        return (CliSettingsSource(settings_cls, add_argument_method=_add_launch_argument),)


_ALIASES = {
    "--port": ("-port", "-p"),
    "--pluginUUID": ("-pluginUUID",),
    "--registerEvent": ("-registerEvent",),
    "--info": ("-info",),
    "--debug": ("-d",),
    "--event-listener-modules": ("--event-listener",),
}


def _add_launch_argument(parser: ArgumentParser, *names: str, **kwargs: Any) -> Any:  # noqa: ANN401
    """Add the host's single-dash long options alongside generated options."""
    aliases = tuple(alias for name in names for alias in _ALIASES.get(name, ()))
    return ArgumentParser.add_argument(parser, *names, *aliases, **kwargs)
