from typing import Any, Literal

from streamdeck.models.events.base import EventBase
from streamdeck.models.events.common import DeviceSpecificEventMixin


class DeviceDidConnect(EventBase, DeviceSpecificEventMixin):
    """Occurs when a Stream Deck device is connected."""
    event: Literal["deviceDidConnect"]  # type: ignore[override]
    deviceInfo: dict[str, Any]
    """Information about the newly connected device."""


class DeviceDidDisconnect(EventBase, DeviceSpecificEventMixin):
    """Occurs when a Stream Deck device is disconnected."""
    event: Literal["deviceDidDisconnect"]  # type: ignore[override]
