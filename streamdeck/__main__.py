"""Parse launch arguments and start the Stream Deck plugin runtime."""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING, TypeVar

from pydantic import ValidationError
from pydantic_settings import SettingsError

from streamdeck.manager import PluginManager
from streamdeck.models.configs import StreamDeckToolConfig
from streamdeck.models.launch import LaunchArguments
from streamdeck.utils.logging import configure_streamdeck_logger


logger = logging.getLogger("streamdeck")
SettingsT = TypeVar("SettingsT")

if TYPE_CHECKING:
    from collections.abc import Callable


def _parse_settings_from_cli(
    settings_cls: Callable[..., SettingsT], args: list[str]
) -> SettingsT:
    """Instantiate Pydantic Settings with its private CLI argument hook."""
    return settings_cls(_cli_parse_args=args)


def main(argv: list[str] | None = None) -> None:
    """Console entry point for the Pydantic Settings CLI."""
    args = sys.argv[1:] if argv is None else list(argv)
    try:
        launch = _parse_settings_from_cli(LaunchArguments, args)
    except (ValidationError, SettingsError) as exc:
        logger.error("Invalid launch arguments: %s", exc)
        raise SystemExit(2) from exc

    try:
        plugin_dir = str(launch.plugin_dir.resolve())
        if plugin_dir not in sys.path:
            sys.path.insert(0, plugin_dir)

        configure_streamdeck_logger(
            name="streamdeck",
            plugin_uuid=launch.info.plugin_uuid,
        )
        if launch.debug_port:
            setup_debug_mode(launch.debug_port)

        config = _parse_settings_from_cli(StreamDeckToolConfig, args)
        run_plugin(launch, config)
    except Exception:
        logger.exception("Plugin startup or execution failed")
        raise


def setup_debug_mode(debug_port: int) -> None:
    """Setup the debug mode for the plugin and wait for the debugger to attach."""
    import debugpy

    debugpy.listen(debug_port)
    logger.info("Starting in debug mode. Waiting for debugger to attach on port %d...", debug_port)
    debugpy.wait_for_client()
    logger.info("Debugger attached.")


def run_plugin(launch: LaunchArguments, config: StreamDeckToolConfig) -> None:
    """Register and run the plugin using validated launch and plugin settings."""
    manager = PluginManager(
        port=launch.port,
        plugin_uuid=launch.info.plugin_uuid,
        plugin_registration_uuid=launch.plugin_registration_uuid,
        register_event=launch.register_event,
        info=launch.info.model_dump(),
    )

    for name, param_config in config.injectable_handler_params.items():
        manager.register_injectable_handler_param_scope(name, param_config.scope)

    # Register custom event types before validating action handlers.
    for listener_type in config.event_listeners:
        manager.register_event_listener(listener_type())

    for action in config.actions:
        manager.register_action(action)

    logger.info("Connecting to Stream Deck on port %d", launch.port)
    manager.run()


# Also run the plugin if this script is ran as a console script.
if __name__ == "__main__":
    main()
