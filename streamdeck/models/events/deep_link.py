from typing import Literal

from streamdeck.models.events.base import ConfiguredBaseModel, EventBase


class DeepLinkPayload(ConfiguredBaseModel):
    """Payload containing information about the URL that triggered the event."""
    url: str
    """The deep-link URL, with the prefix omitted."""


class DidReceiveDeepLink(EventBase):
    """Occurs when Stream Deck receives a deep-link message intended for the plugin.

    The message is re-routed to the plugin, and provided as part of the payload.
    One-way deep-link message can be routed to the plugin using the URL format:
    streamdeck://plugins/message/<PLUGIN_UUID>/{MESSAGE}.
    """
    event: Literal["didReceiveDeepLink"]  # type: ignore[override]
    payload: DeepLinkPayload
    """Payload containing information about the URL that triggered the event."""
