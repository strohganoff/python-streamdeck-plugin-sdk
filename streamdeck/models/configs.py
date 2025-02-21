from __future__ import annotations

from types import ModuleType
from typing import TYPE_CHECKING, Annotated

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


if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path
    from typing import Any




class PyProjectConfigs(BaseModel):
    """A Pydantic model for the PyProject.toml configuration file to load a Stream Deck plugin's actions."""
    tool: ToolSection = Field(alias="tool")

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
    def streamdeck_plugin_actions(self) -> Generator[ActionBase, Any, None]:
        """Reach into the [tool.streamdeck] section of the PyProject.toml file and yield the plugin's actions configured by the developer."""
        for loaded_action_script in self.tool.streamdeck.action_script_modules:
            for object_name in dir(loaded_action_script):
                obj = getattr(loaded_action_script, object_name)

                # Ensure the object isn't a magic method or attribute of the loaded module.
                if object_name.startswith("__"):
                    continue

                yield obj


class ToolSection(BaseModel):
    """A model class representing the "tool" section in configuration.

    Nothing much to see here, just a wrapper around the model representing the "streamdeck" subsection.
    """
    streamdeck: StreamDeckToolConfig


class StreamDeckToolConfig(BaseModel, arbitrary_types_allowed=True):
    """A model class representing the "streamdeck" subsection in the "tool" section of the PyProject.toml file.

    This section contains the developer's configuration for their Stream Deck plugin.
    """
    action_script_modules: Annotated[list[ImportString[ModuleType]], Field(alias="action_scripts")]
    """A list of loaded action script modules with all of their objects.

    This field is filtered to only include objects that are subclasses of ActionBase (as well as the built-in magic methods and attributes typically found in a module).
    """

    @field_validator("action_script_modules", mode="after")
    @classmethod
    def filter_module_objects(cls, value: list[ModuleType]) -> list[ModuleType]:
        """Filter out non- ActionBase subclasses from the list of objects loaded from each action script module."""
        loaded_modules: list[ModuleType] = []

        for module in value:
            new_module = ModuleType(module.__name__)

            for object_name in dir(module):
                obj = getattr(module, object_name)

                if not isinstance(obj, ActionBase):
                    continue

                setattr(new_module, object_name, obj)

            loaded_modules.append(new_module)

        return loaded_modules


