from __future__ import annotations

from types import ModuleType  # noqa: TC003
from typing import TYPE_CHECKING, Annotated, ClassVar

import tomli as toml
from pydantic import (
    BaseModel,
    Field,
    ImportString,
    ValidationInfo,
    field_validator,
    model_validator,
)

from streamdeck.actions import ActionBase
from streamdeck.event_listener import EventListener
from streamdeck.models.events import EventBase


if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path



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


class PyProjectConfigs(BaseModel):
    """A Pydantic model for the PyProject.toml configuration file to load a Stream Deck plugin's actions."""
    tool: ToolSection
    """The "tool" section of a pyproject.toml file, which contains configs for project tools, including for this Stream Deck plugin."""

    @classmethod
    def validate_from_toml_file(cls, filepath: Path, action_scripts: list[str] | None = None) -> PyProjectConfigs:
        """Alternative constructor to validate a PyProjectConfigs instance from a TOML file."""
        with filepath.open("rb") as f:
            pyproject_configs = toml.load(f)

            # Pass the action scripts to the context dictionary if they are provided,
            # so they can be used in the before-validater for the nested StreamDeckToolConfig model.
            ctx = {"action_scripts": action_scripts} if action_scripts else None

            # Return the loaded PyProjectConfigs model instance.
            return cls.model_validate(pyproject_configs, context=ctx)

    @model_validator(mode="before")
    @classmethod
    def overwrite_action_scripts(cls, data: object, info: ValidationInfo) -> object:
        """If action scripts were provided as a context variable, overwrite the action_scripts field in the PyProjectConfigs model."""
        context = info.context

        # If no action scripts were provided, return the data as-is.
        if context is None or "action_scripts" not in context:
            return data

        # If data isn't a dict as expected, let Pydantic's validation handle them as usual in its next validations step.
        if isinstance(data, dict):
            # We also need to ensure the "tool" and "streamdeck" sections exist in the data dictionary in case they were not defined in the PyProject.toml file.
            data.setdefault("tool", {}).setdefault("streamdeck", {})["action_scripts"] = context["action_scripts"]

        return data

    @property
    def streamdeck(self) -> StreamDeckToolConfig:
        """Reach into the [tool.streamdeck] section of the PyProject.toml file and return the plugin's configuration."""
        return self.tool.streamdeck

    @property
    def streamdeck_plugin_actions(self) -> Generator[ActionBase, None, None]:
        """Reach into the [tool.streamdeck] section of the PyProject.toml file and yield the plugin's actions configured by the developer."""
        yield from self.streamdeck.actions

    @property
    def event_listeners(self) -> Generator[type[EventListener], None, None]:
        """Reach into the [tool.streamdeck] section of the PyProject.toml file and yield the plugin's event listeners configured by the developer."""
        yield from self.streamdeck.event_listeners

    @property
    def event_models(self) -> Generator[type[EventBase], None, None]:
        """Reach into the [tool.streamdeck] section of the PyProject.toml file and yield the plugin's event models configured by the developer."""
        yield from self.streamdeck.event_models


class ToolSection(BaseModel):
    """A model class representing the "tool" section in configuration.

    Nothing much to see here, just a wrapper around the model representing the "streamdeck" subsection.
    """
    streamdeck: StreamDeckToolConfig
    """The "streamdeck" subsection in the "tool" section of the pyproject.toml file, which contains the developer's configuration for their Stream Deck plugin."""


class StreamDeckToolConfig(BaseModel, arbitrary_types_allowed=True):
    """A model class representing the "streamdeck" subsection in the "tool" section of the PyProject.toml file.

    This section contains the developer's configuration for their Stream Deck plugin.
    """
    action_script_modules: Annotated[list[ImportString[ModuleType]], Field(alias="action_scripts")]
    """A list of loaded action script modules with all of their objects.

    This field is filtered to only include objects that are subclasses of ActionBase (as well as the built-in magic methods and attributes typically found in a module).
    """

    event_listener_modules: list[ImportString[ModuleType]] = []
    """A list of loaded event listener modules with all of their objects.

    This field is filtered to only include objects that are subclasses of EventListener & EventBase (as well as the built-in magic methods and attributes typically found in a module).
    """

    # The following fields are populated by the field validators below, and are not during Pydantic's validation process.
    actions: ClassVar[list[ActionBase]] = []
    """The collected ActionBase subclass instances from the loaded modules listed in the `action_script_modules` field."""
    event_listeners: ClassVar[list[type[EventListener]]] = []
    """The collected EventListener subclasses from the loaded modules listed in the `event_listener_modules` field."""
    event_models: ClassVar[list[type[EventBase]]] = []
    """The collected EventBase subclasses from the loaded modules listed in the `event_listener_modules` field."""

    @field_validator("action_script_modules", mode="after")
    @classmethod
    def filter_action_module_objects(cls, value: list[ModuleType]) -> list[ModuleType]:
        """Loop through objects in each configured action script module, and collect ActionBase subclasses.

        The value arg isn't modified here, it is simply returned as-is at the end of the method.
        """
        for obj in parse_objects_from_modules(value):
            # Ignore obj if it's not an instance of an ActionBase subclass.
            if not isinstance(obj, ActionBase):
                continue

            cls.actions.append(obj)

        return value

    @field_validator("event_listener_modules", mode="after")
    @classmethod
    def filter_event_listener_module_objects(cls, value: list[ModuleType]) -> list[ModuleType]:
        """Loop through objects in each configured event listener module, and collect EventListener and EventBase subclasses.

        The value arg isn't modified here, it is simply returned as-is at the end of the method.
        """
        for obj in parse_objects_from_modules(value):
            # Ensure obj is a type (class definition), but not the base classes themselves.
            if not isinstance(obj, type) or obj in (EventListener, EventBase):
                continue

            # Collect obj if it is an EventListener subclass
            if issubclass(obj, EventListener):
                cls.event_listeners.append(obj)

            # Collect obj if it is an EventBase subclass
            if issubclass(obj, EventBase):
                cls.event_models.append(obj)

        return value
