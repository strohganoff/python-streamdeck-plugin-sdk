"""This module provides utility functions for configuring loggers for Elgato Stream Deck plugins.

The module includes functions to set up loggers that write logs to either the centralized Stream Deck user log directory
or to the installed plugin's local code directory. Each logger is configured with both a stream handler for console output and a
rotating file handler to manage log file sizes.
"""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from streamdeck.utils.dirs import plugin_local_data_dir, streamdeck_log_dir


def configure_streamdeck_logger(
    name: str,
    plugin_uuid: str,
    log_level: int = logging.DEBUG,
) -> None:
    """Configure a logger for the Elgato Stream Deck plugin with a rotating file handler.

    This logger writes to a log file located in the Stream Deck user log directory, where both internal Stream Deck components
    and plugins have their logs centralized.

    Args:
        name (str): The name of the logger.
        plugin_uuid (str): The UUID of the plugin.
        log_level (int, optional): The logging level. Defaults to logging.DEBUG.
    """
    plugin_log_filepath = streamdeck_log_dir() / f"{plugin_uuid}.log"

    _configure_logger(
        name=name,
        filename=plugin_log_filepath,
        level=log_level,
    )


def configure_local_logger(
    name: str,
    plugin_uuid: str,
    log_level: int = logging.DEBUG,
) -> None:
    """Configure a logger for a Stream Deck plugin that writes to a local data directory.

    This logger writes to a log file located in the local plugin directory, allowing plugin-specific logs to be kept
    separately from the main Stream Deck logs.

    Args:
        name (str): The name of the logger.
        plugin_uuid (str): The UUID of the plugin.
        log_level (int, optional): The logging level. Defaults to logging.DEBUG.
    """
    # The log file name is the last component of the plugin_uuid.
    plugin_component_name = plugin_uuid.split(".")[-1]

    local_log_filepath = (
        plugin_local_data_dir(plugin_uuid=plugin_uuid) / f"logs/{plugin_component_name}.log"
    )

    _configure_logger(
        name=name,
        filename=local_log_filepath,
        level=log_level,
    )


def _configure_logger(
    name: str,
    filename: Path,
    level: int = logging.DEBUG,
) -> logging.Logger:
    """Helper function to configure a logger with a stream handler and a rotating file handler.

    This function ensures that the logger is only configured once by checking its handlers. It sets up both a stream
    handler for console output and a rotating file handler to save logs to a file.

    Args:
        name (str): The name of the logger.
        filename (Path): The path to the log file.
        level (int, optional): The logging level. Defaults to logging.DEBUG.

    Returns:
        logging.Logger: The configured logger instance.
    """
    logger = logging.getLogger(name)

    # For some reason, logger.getHandlers() evaluates as True here, even if the handlers list property is empty...
    if not logger.handlers:
        logger.setLevel(level)

        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        # Ensure the directory path this logger will write files to exists.
        filename.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            filename.expanduser(),
            maxBytes=5 * 1024 * 1024,
            backupCount=20,
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
