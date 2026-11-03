"""TOML-only plugin settings and module discovery."""

from __future__ import annotations

from contextvars import ContextVar
from pathlib import Path  # noqa: TC003
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


_load_options: ContextVar[tuple[Path | None, list[str] | None]] = ContextVar(
    "streamdeck_toml_load_options",
    default=(None, None),
)


def parse_objects_from_modules(value: list[ModuleType]) -> Generator[object, None, None]:
    """Loop through objects in each provided module to be yielded.

    Methods and attributes that are magic, special, or built-in are ignored.
    """
    for module in value:
        for object_name in dir(module):
            obj = getattr(module, object_name)

            # Ignore magic/special/built-in methods and attributes.
            if object_name.startswith("__"):
                continue

            yield obj


class StreamDeckToolConfig(BaseSettings):
    """Plugin configuration loaded exclusively from [tool.streamdeck]."""

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
        init_settings: PydanticBaseSettingsSource,  # noqa: ARG003 - required hook parameter
        env_settings: PydanticBaseSettingsSource,  # noqa: ARG003 - required hook parameter
        dotenv_settings: PydanticBaseSettingsSource,  # noqa: ARG003 - required hook parameter
        file_secret_settings: PydanticBaseSettingsSource,  # noqa: ARG003 - required hook parameter
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Use only TOML; Typer overrides its data explicitly until CLI migration."""
        filepath, action_scripts = _load_options.get()
        # The settings source otherwise silently ignores a missing file.
        if filepath is not None:
            with filepath.open("rb"):
                pass
        source = PyprojectTomlConfigSettingsSource(settings_cls, filepath)
        if action_scripts:
            source.init_kwargs["action_scripts"] = action_scripts
        return (source,)

    def __init__(
        self,
        *,
        toml_file: Path | None = None,
        action_scripts_override: list[str] | None = None,
        **values: object,
    ) -> None:
        """Configure the TOML source before settings validation.

        These keyword arguments control loading, not model fields. Other constructor
        field values are ignored because InitSettingsSource is not enabled.
        A scoped context passes options to the class-level source hook and is reset
        even when validation or a nested configuration load fails.
        """
        token = _load_options.set((toml_file, action_scripts_override))
        try:
            super().__init__(**values)
        finally:
            _load_options.reset(token)

    @property
    def actions(self) -> list[ActionBase]:
        """Discover action instances from this configuration's modules."""
        return [
            obj
            for obj in parse_objects_from_modules(self.action_script_modules)
            if isinstance(obj, ActionBase)
        ]

    @property
    def event_listeners(self) -> list[type[EventListener]]:
        """Discover listener classes, including imported classes, except the base."""
        return [
            obj
            for obj in parse_objects_from_modules(self.event_listener_modules)
            if isinstance(obj, type) and obj is not EventListener and issubclass(obj, EventListener)
        ]

    @property
    def event_models(self) -> list[type[EventBase]]:
        """Discover event classes, including imported classes, except the base."""
        return [
            obj
            for obj in parse_objects_from_modules(self.event_listener_modules)
            if isinstance(obj, type) and obj is not EventBase and issubclass(obj, EventBase)
        ]
