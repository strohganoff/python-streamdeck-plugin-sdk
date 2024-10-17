from __future__ import annotations

from typing import TYPE_CHECKING

import platformdirs


if TYPE_CHECKING:
    from pathlib import Path



def streamdeck_log_dir() -> Path:
    return platformdirs.user_log_path(appname="ElgatoStreamDeck")


def streamdeck_local_data_dir() -> Path:
    return platformdirs.user_data_path("com.elgato.StreamDeck")


def plugin_local_data_dir(plugin_name: str) -> Path:
    return streamdeck_local_data_dir() / "Plugins" / plugin_name


def streamdeck_application_data_dir() -> Path:
    # NOTE: The only directory under this seems to be "QtWebEngine",
    # which is a component for embeding web browser functionality into their desktop applications.
    return platformdirs.user_data_path('elgato') / "Streamdeck"


def plugin_application_data_dir(plugin_name: str) -> Path:
    # NOTE: Not all plugins have a directory here.. A few individual plugins have probably pushed data to this location.
    return streamdeck_application_data_dir() / "QtWebEngine" / plugin_name


def elgato_site_data_dir() -> Path:
    # NOTE: There doesn't seem to be a "Stream Deck" directory in here, just "Wave Link".
    return platformdirs.site_data_path("Elgato")