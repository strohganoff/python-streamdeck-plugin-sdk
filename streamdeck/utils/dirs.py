"""This module provides utility functions to get various directory paths related to Elgato Stream Deck plugins and components.

The functions defined here help locate user-specific log directories, local data directories for plugins, and application data directories for Elgato Stream Deck components and plugins.
These paths are useful for accessing log files, unpacked plugin code, and other application data for Stream Deck and its plugins.

Note:
    These functions have been tested on macOS only so far, with plans to test on Windows in the future.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import platformdirs


if TYPE_CHECKING:
    from pathlib import Path



def streamdeck_log_dir() -> Path:
    """Get the path to the user-specific log directory for Elgato Stream Deck.

    The result of this function is the user log directory path that all plugins as well as internal StreamDeck components write to.

    Returns:
        Path: Path to the Stream Deck log directory.
    """
    return platformdirs.user_log_path(appname="ElgatoStreamDeck")


def streamdeck_local_data_dir() -> Path:
    """Get the path to the local user-specific data directory for Elgato Stream Deck.

    The result of this function is the directory that contains the unpacked (i.e. unzipped) directories of all of the code of installed plugins.

    Returns:
        Path: Path to the local data directory for Stream Deck.
    """
    return platformdirs.user_data_path("com.elgato.StreamDeck")


def plugin_local_data_dir(plugin_uuid: str) -> Path:
    """Get the path to the local user-specific data directory for a specific Stream Deck plugin.

    The result of this function is the directory path for the given plugin's unpacked (i.e. unzipped) code.

    Args:
        plugin_uuid (str): The UUID of the plugin.

    Returns:
        Path: Path to the local data directory for the specified plugin.
    """
    return streamdeck_local_data_dir() / "Plugins" / f"{plugin_uuid}.sdPlugin"


def streamdeck_application_data_dir() -> Path:
    """Get the path to the application-specific data directory for Elgato Stream Deck.

    Note:
        The only directory under this path seems to be "QtWebEngine", which is a component for embedding web browser
        functionality into their desktop applications.

    Returns:
        Path: Path to the application data directory for Stream Deck.
    """
    return platformdirs.user_data_path("elgato") / "Streamdeck"


def plugin_application_data_dir(plugin_uuid: str) -> Path:
    """Get the path to the application-specific data directory for a specific Stream Deck plugin.

    Note:
        Not all plugins have a directory here. Only a few individual plugins have likely pushed data to this location.

    Args:
        plugin_uuid (str): The UUID of the plugin.

    Returns:
        Path: Path to the application data directory for the specified plugin.
    """
    return streamdeck_application_data_dir() / "QtWebEngine" / plugin_uuid


def elgato_site_data_dir() -> Path:
    """Get the path to the system-wide shared data directory for Elgato products.

    Note:
        There doesn't seem to be a "Stream Deck" directory in here, only "Wave Link".

    Returns:
        Path: Path to the shared data directory for Elgato products.
    """
    return platformdirs.site_data_path("Elgato")
