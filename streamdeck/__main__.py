from __future__ import annotations

import json
import logging
import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import cast

from streamdeck.cli.errors import (
    DirectoryNotFoundError,
)
from streamdeck.cli.models import (
    CliArgsNamespace,
)
from streamdeck.manager import PluginManager
from streamdeck.models.configs import PyProjectConfigs
from streamdeck.utils.logging import configure_streamdeck_logger


logger = logging.getLogger("streamdeck")



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
    parser.add_argument(
        "-pluginUUID", dest="pluginUUID", type=str, help="pluginUUID", required=True
    )
    parser.add_argument(
        "-registerEvent", dest="registerEvent", type=str, help="registerEvent", required=True
    )
    parser.add_argument("-info", dest="info", type=str, help="info", required=True)

    return parser


def main():
    """Main function to parse arguments, load actions, and execute them."""
    parser = setup_cli()
    args = cast(CliArgsNamespace, parser.parse_args())

    # If `plugin_dir` was not passed in as a cli option, then fall back to using the CWD.
    if args.plugin_dir is None:
        plugin_dir = Path.cwd()
    # Also validate the plugin_dir argument.
    elif not args.plugin_dir.is_dir():
        msg = f"The provided plugin directory '{args.plugin_dir}' is not a directory."
        raise NotADirectoryError(msg)
    elif not args.plugin_dir.exists():
        msg = f"The provided plugin directory '{args.plugin_dir}' does not exist."
        raise DirectoryNotFoundError(msg, directory=args.plugin_dir)
    else:
        plugin_dir = args.plugin_dir

    # Ensure plugin_dir is in `sys.path`, so that import statements in the plugin module will work as expected.
    if str(plugin_dir) not in sys.path:
        sys.path.insert(0, str(plugin_dir))

    info = json.loads(args.info)
    plugin_uuid = info["plugin"]["uuid"]

    # After configuring once here, we can grab the logger in any other module with `logging.getLogger("streamdeck")`, or
    # a child logger with `logging.getLogger("streamdeck.mycomponent")`, all with the same handler/formatter configuration.
    configure_streamdeck_logger(name="streamdeck", plugin_uuid=plugin_uuid)

    pyproject = PyProjectConfigs.validate_from_toml_file(plugin_dir / "pyproject.toml")
    actions = list(pyproject.streamdeck_plugin_actions)

    manager = PluginManager(
        port=args.port,
        plugin_uuid=plugin_uuid,
        # NOT the configured plugin UUID in the manifest.json,
        # which can be pulled out of `info["plugin"]["uuid"]`
        plugin_registration_uuid=args.pluginUUID,
        register_event=args.registerEvent,
        info=info,
    )

    for action in actions:
        manager.register_action(action)

    manager.run()


if __name__ == "__main__":
    main()
