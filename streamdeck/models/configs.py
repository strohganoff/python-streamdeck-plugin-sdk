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

            # Pass the action scripts to the context dictionary if they are provided, so they can be used in the before-validater for the nested StreamDeckToolConfig model.
            ctx = {"action_scripts": action_scripts} if action_scripts else None

            # Return the loaded PyProjectConfigs model instance.
            return cls.model_validate(pyproject_configs, context=ctx)

    @property
    def streamdeck_plugin_actions(self) -> Generator[type[ActionBase], Any, None]:
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

    @field_validator("action_script_modules", mode="before")
    @classmethod
    def overwrite_action_scripts_with_user_provided_data(cls, value: list[str], info: ValidationInfo) -> list[str]:
        """Overwrite the list of action script modules with the user-provided data.

        NOTE: This is a before-validator that runs before the next field_validator method on the same field.
        """
        # If the user provided action_scripts to load, use that instead of the value from the PyProject.toml file.
        if info.context is not None and "action_scripts" in info.context:
            return info.context["action_scripts"]

        return value

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


