"""Plugin settings from CLI arguments and TOML, with module discovery."""

from __future__ import annotations

from functools import cached_property
from types import ModuleType  # noqa: TC003
from typing import TYPE_CHECKING, Annotated

from pydantic import (
    Field,
    ImportString,
)
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    PyprojectTomlConfigSettingsSource,
    SettingsConfigDict,
)

from streamdeck.event_handlers.actions import ActionBase
from streamdeck.event_listener import EventListener
from streamdeck.models.events import EventBase


if TYPE_CHECKING:
    from collections.abc import Generator


def iter_module_objects(module: ModuleType) -> Generator[object, None, None]:
    """Yield module namespace values whose names do not start with double underscores."""
    for object_name, obj in vars(module).items():
        if object_name.startswith("__"):
            continue

        yield obj


class StreamDeckToolConfig(BaseSettings):
    """Plugin configuration from CLI values followed by [tool.streamdeck]."""

    model_config = SettingsConfigDict(
        arbitrary_types_allowed=True,
        extra="ignore",
        pyproject_toml_table_header=("tool", "streamdeck"),
    )

    action_script_modules: Annotated[list[ImportString[ModuleType]], Field(alias="action_scripts")]
    event_listener_modules: list[ImportString[ModuleType]] = Field(default_factory=list)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        **_sources: PydanticBaseSettingsSource,
    ) -> tuple[PyprojectTomlConfigSettingsSource]:
        """Use CLI and TOML without environment, constructor, or secrets sources."""
        return (PyprojectTomlConfigSettingsSource(settings_cls),)

    @cached_property
    def actions(self) -> list[ActionBase]:
        """Discover action instances from this configuration's modules."""
        return [
            obj
            for module in self.action_script_modules
            for obj in iter_module_objects(module)
            if isinstance(obj, ActionBase)
        ]

    @cached_property
    def _event_listener_objects(self) -> tuple[object, ...]:
        """Collect listener-module objects once for both discovery properties."""
        return tuple(
            obj
            for module in self.event_listener_modules
            for obj in iter_module_objects(module)
        )

    @cached_property
    def event_listeners(self) -> list[type[EventListener]]:
        """Discover listener classes, including imported classes, except the base."""
        return [
            obj
            for obj in self._event_listener_objects
            if isinstance(obj, type) and obj is not EventListener and issubclass(obj, EventListener)
        ]

    @cached_property
    def event_models(self) -> list[type[EventBase]]:
        """Discover event classes, including imported classes, except the base."""
        return [
            obj
            for obj in self._event_listener_objects
            if isinstance(obj, type) and obj is not EventBase and issubclass(obj, EventBase)
        ]
