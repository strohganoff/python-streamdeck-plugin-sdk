import json
import logging
import sys
from pathlib import Path
from typing import Annotated, Optional

import typer

from streamdeck.manager import PluginManager
from streamdeck.models.configs import PyProjectConfigs
from streamdeck.utils.logging import configure_streamdeck_logger


logger = logging.getLogger("streamdeck")



plugin = typer.Typer()


def setup_debug_mode(debug_port: int) -> None:
    """Setup the debug mode for the plugin and wait for the debugger to attach."""
    import debugpy

    debugpy.listen(debug_port)
    logger.info("Starting in debug mode. Waiting for debugger to attach on port %d...", debug_port)
    debugpy.wait_for_client()
    logger.info("Debugger attached.")


@plugin.command()
def main(
    port: Annotated[int, typer.Option("-p", "-port")],
    plugin_registration_uuid: Annotated[str, typer.Option("-pluginUUID")],
    register_event: Annotated[str, typer.Option("-registerEvent")],
    info: Annotated[str, typer.Option("-info")],
    plugin_dir: Annotated[Path, typer.Option(file_okay=False, exists=True, readable=True)] = Path.cwd(),  # noqa: B008
    action_scripts: Optional[list[str]] = None,  # noqa: UP007
    debug_port: Annotated[Optional[int], typer.Option("--debug", "-d")] = None,  # noqa: UP007
) -> None:
    """Start the Stream Deck plugin with the given configuration.

    NOTE: Single flag long-name options are extected & passed in by the Stream Deck software.
    Double flag long-name options are used during development and testing.
    """
    # Ensure plugin_dir is in `sys.path`, so that import statements in the plugin module will work as expected.
    if str(plugin_dir) not in sys.path:
        sys.path.insert(0, str(plugin_dir))

    info_data = json.loads(info)
    plugin_uuid = info_data["plugin"]["uuid"]

    # After configuring once here, we can grab the logger in any other module with `logging.getLogger("streamdeck")`, or
    # a child logger with `logging.getLogger("streamdeck.mycomponent")`, all with the same handler/formatter configuration.
    configure_streamdeck_logger(name="streamdeck", plugin_uuid=plugin_uuid)

    logger.info("Stream Deck listening to plugin UUID '%s' on port %d", plugin_uuid, port)

    if debug_port:
        setup_debug_mode(debug_port)

    pyproject = PyProjectConfigs.validate_from_toml_file(plugin_dir / "pyproject.toml", action_scripts=action_scripts)
    actions = pyproject.streamdeck_plugin_actions

    manager = PluginManager(
        port=port,
        plugin_uuid=plugin_uuid,
        # NOT the configured plugin UUID in the manifest.json,
        # which can be pulled out of `info["plugin"]["uuid"]`
        plugin_registration_uuid=plugin_registration_uuid,
        register_event=register_event,
        info=info_data,
    )

    # Event listeners and their Event models are registered before actions in order to validate the actions' registered events' names.
    for event_listener in pyproject.event_listeners:
        manager.register_event_listener(event_listener())

    for action in actions:
        manager.register_action(action)

    try:
        manager.run()
    except Exception as e:
        logger.exception("Error in plugin manager")
        raise


# Also run the plugin if this script is ran as a console script.
if __name__ in ("__main__", "streamdeck.__main__"):
    plugin()



