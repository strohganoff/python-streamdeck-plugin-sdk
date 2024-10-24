from __future__ import annotations

import importlib.util
import json
import logging
import os
from argparse import ArgumentParser
from pathlib import Path
from typing import TYPE_CHECKING, cast

import tomli as toml

from streamdeck.actions import Action
from streamdeck.cli.errors import (
    DirectoryNotFoundError,
    NotAFileError,
)
from streamdeck.cli.models import (
    CliArgsNamespace,
    PyProjectConfigDict,
    StreamDeckConfigDict,
)
from streamdeck.manager import PluginManager


if TYPE_CHECKING:
    from collections.abc import Generator  # noqa: I001
    from importlib.machinery import ModuleSpec
    from types import ModuleType
    from typing_extensions import Self  # noqa: UP035


logger = logging.getLogger("streamdeck-plugin-sdk")

logger.addHandler(logging.StreamHandler())

# TODO: Add better functionality for setting up logging to save to files in the proper streamdeck log directory.
file_handler = logging.FileHandler(os.path.expanduser("~/plugin.log"))
file_handler.setLevel(logging.DEBUG)
logger.addHandler(file_handler)

logger.info("Starting run...")


def setup_cli() -> ArgumentParser:
    """Set up the command-line interface for the script.

    Returns:
        argparse.ArgumentParser: The argument parser for the CLI.
    """
    parser = ArgumentParser(description="CLI to load Actions from action scripts.")
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        "plugin_dir",
        type=Path,
        nargs="?",
        help="The directory containing plugin files to load Actions from.",
    )
    group.add_argument(
        "--action-scripts",
        type=str,
        nargs="+",
        help="A list of action script file paths to load Actions from or a single value to be processed.",
    )

    # Options that will always be passed in by the StreamDeck software when running this plugin.
    parser.add_argument("-port", dest="port", type=int, help="Port", required=True)
    parser.add_argument("-pluginUUID", dest="pluginUUID", type=str, help="pluginUUID", required=True)
    parser.add_argument("-registerEvent", dest="registerEvent", type=str, help="registerEvent", required=True)
    parser.add_argument("-info", dest="info", type=str, help="info", required=True)

    return parser


def determine_action_scripts(plugin_dir: Path | None, action_scripts: list[str] | None) -> list[str]:
    """Determine the action scripts to be loaded based on provided arguments.

    plugin_dir and action_scripts cannot both have values -> either only one of them isn't None, or they are both None.

    Args:
        plugin_dir (Path | None): The directory containing plugin files to load Actions from.
        action_scripts (list[str] | None): A list of action script file paths.

    Returns:
        list[str]: A list of action script file paths.

    Raises:
        KeyError: If the 'action_scripts' setting is missing from the streamdeck config.
    """
    # If `action_scripts` arg was provided, then we can ignore plugin_dir (because we can assume plugin_dir is None).
    if action_scripts is not None:
        return action_scripts

    # If `action_scripts` is None, then either plugin_dir has a value or it is None.
    # Thus either use the value given to plugin_value if it was given one, or fallback to using the current working directory.
    streamdeck_config = read_streamdeck_config_from_pyproject(plugin_dir=plugin_dir or Path.cwd())
    try:
        return streamdeck_config["action_scripts"]

    except KeyError as e:
        msg = f"'action_plugin' setting missing from streamdeck config in pyproject.toml in '{args.plugin_dir}'."
        raise KeyError(msg) from e



def read_streamdeck_config_from_pyproject(plugin_dir: Path) -> StreamDeckConfigDict:
    """Get the streamdeck section from a plugin directory by reading pyproject.toml.

    Plugin devs add a section to their pyproject.toml for "streamdeck" to configure setup for their plugin.

    Args:
        plugin_dir (Path): The directory containing the pyproject.toml and plugin files.

    Returns:
        List[Path]: A list of file paths found in the specified scripts.

    Raises:
        DirectoryNotFoundError: If the specified plugin_dir does not exist.
        NotADirectoryError: If the specified plugin_dir is not a directory.
        FileNotFoundError: If the pyproject.toml file does not exist in the plugin_dir.
    """
    if not plugin_dir.exists():
        msg = f"The directory '{plugin_dir}' does not exist."
        raise DirectoryNotFoundError(msg, directory=plugin_dir)

    pyproject_path = plugin_dir / "pyproject.toml"
    with pyproject_path.open("rb") as f:
        try:
            pyproject_config: PyProjectConfigDict = toml.load(f)

        except FileNotFoundError as e:
            msg = f"There is no 'pyproject.toml' in the given directory '{plugin_dir}"
            raise FileNotFoundError(msg) from e

        except NotADirectoryError as e:
            msg = f"The provided directory exists but is not a directory: '{plugin_dir}'."
            raise NotADirectoryError(msg) from e

        try:
            streamdeck_config = pyproject_config["tool"]["streamdeck"]

        except KeyError as e:
            msg = f"Section 'tool.streamdeck' is missing from '{pyproject_path}'."
            raise KeyError(msg) from e

        return streamdeck_config


class ActionLoader:
    @classmethod
    def load_actions(cls: type[Self], files: list[str]) -> Generator[Action, None, None]:
        for action_script in files:
            module = cls._load_module_from_file(filepath=Path(action_script))
            yield from cls._get_actions_from_loaded_module(module=module)

    @staticmethod
    def _load_module_from_file(filepath: Path) -> ModuleType:
        """Load module from a given Python file.

        Args:
            filepath (str): The path to the Python file.

        Returns:
            ModuleType: A loaded module located at the specified filepath.

        Raises:
            FileNotFoundError: If the specified file does not exist.
            NotAFileError: If the specified file exists, but is not a file.
        """
        # First validate the filepath arg here.
        if not filepath.exists():
            msg = f"The file '{filepath}' does not exist."
            raise FileNotFoundError(msg)
        if not filepath.is_file():
            msg = f"The provided filepath '{filepath}' is not a file."
            raise NotAFileError(msg)

        # Create a module specification for a module located at the given filepath.
        # A "specification" is an object that contains information about how to load the module, such as its location and loader.
        # "module.name" is an arbitrary name used to identify the module internally.
        spec: ModuleSpec = importlib.util.spec_from_file_location("module.name", str(filepath)) # type: ignore
        # Create a new module object from the given specification.
        # At this point, the module is created but not yet loaded (i.e. its code hasn't been executed).
        module: ModuleType = importlib.util.module_from_spec(spec)
        # Load the module by executing its code, making available its functions, classes, and variables.
        spec.loader.exec_module(module) # type: ignore

        return module

    @staticmethod
    def _get_actions_from_loaded_module(module: ModuleType) -> Generator[Action, None, None]:
        # Iterate over all attributes in the module to find Action subclasses
        for attribute_name in dir(module):
            attribute = getattr(module, attribute_name)
            # Check if the attribute is an instance of the Action class
            if isinstance(attribute, Action):
                yield attribute


def main():
    """Main function to parse arguments, load actions, and execute them."""
    parser = setup_cli()
    args = cast(CliArgsNamespace, parser.parse_args())

    info = json.loads(args.info)
    plugin_name = info["plugin"]["uuid"]

    action_scripts = determine_action_scripts(
        plugin_dir=args.plugin_dir,
        action_scripts=args.action_scripts,
    )

    actions = list(ActionLoader.load_actions(files=action_scripts))

    manager = PluginManager(
        port=args.port,
        plugin_uuid=args.pluginUUID,
        register_event=args.registerEvent,
        info=info,
    )

    for action in actions:
        manager.register_action(action)

    manager.run()


if __name__ == "__main__":
    main()
