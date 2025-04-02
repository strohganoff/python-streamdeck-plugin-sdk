from typing import Literal

from streamdeck.models.events.base import EventBase


class DidReceiveDeepLink(EventBase):
    """Occurs when Stream Deck receives a deep-link message intended for the plugin.

    The message is re-routed to the plugin, and provided as part of the payload.
    One-way deep-link message can be routed to the plugin using the URL format:
    streamdeck://plugins/message/<PLUGIN_UUID>/{MESSAGE}.
    """
    event: Literal["didReceiveDeepLink"]  # type: ignore[override]
    payload: dict[Literal["url"], str]
    """Payload containing information about the URL that triggered the event."""
