"""Parse launch arguments and start the Stream Deck plugin runtime."""

import logging
import sys

from streamdeck.manager import PluginManager
from streamdeck.models.configs import StreamDeckToolConfig
from streamdeck.models.launch import LaunchArguments, parse_launch_arguments
from streamdeck.utils.logging import configure_streamdeck_logger


logger = logging.getLogger("streamdeck")


def plugin() -> None:
    """Console entry point for the Pydantic Settings CLI."""
    main(parse_launch_arguments())


def setup_debug_mode(debug_port: int) -> None:
    """Setup the debug mode for the plugin and wait for the debugger to attach."""
    import debugpy

    debugpy.listen(debug_port)
    logger.info("Starting in debug mode. Waiting for debugger to attach on port %d...", debug_port)
    debugpy.wait_for_client()
    logger.info("Debugger attached.")


def main(launch: LaunchArguments) -> None:
    """Start the plugin after CLI validation."""
    plugin_dir = launch.plugin_dir
    port = launch.port
    debug_port = launch.debug_port
    # Ensure plugin_dir is in `sys.path`, so that import statements in the plugin module will work as expected.
    if str(plugin_dir) not in sys.path:
        sys.path.insert(0, str(plugin_dir))

    info_data = launch.info
    plugin_uuid = info_data["plugin"]["uuid"]

    # After configuring once here, we can grab the logger in any other module with `logging.getLogger("streamdeck")`, or
    # a child logger with `logging.getLogger("streamdeck.mycomponent")`, all with the same handler/formatter configuration.
    configure_streamdeck_logger(name="streamdeck", plugin_uuid=plugin_uuid)

    logger.info("Stream Deck listening to plugin UUID '%s' on port %d", plugin_uuid, port)

    if debug_port:
        setup_debug_mode(debug_port)

    config = StreamDeckToolConfig(_cli_settings_source=launch.cli_settings_source)

    manager = PluginManager(
        port=port,
        plugin_uuid=plugin_uuid,
        # NOT the configured plugin UUID in the manifest.json,
        # which can be pulled out of `info["plugin"]["uuid"]`
        plugin_registration_uuid=launch.plugin_registration_uuid,
        register_event=launch.register_event,
        info=info_data,
    )

    # Event listeners and their Event models are registered before actions in order to validate the actions' registered events' names.
    for event_listener in config.event_listeners:
        manager.register_event_listener(event_listener())

    for action in config.actions:
        manager.register_action(action)

    try:
        manager.run()
    except Exception:
        logger.exception("Error in plugin manager")
        raise


# Also run the plugin if this script is ran as a console script.
if __name__ == "__main__":
    plugin()
