from typing import Any, Literal

from streamdeck.models.events.base import EventBase
from streamdeck.models.events.common import DeviceSpecificEventMixin


class DeviceDidConnect(EventBase, DeviceSpecificEventMixin):
    event: Literal["deviceDidConnect"]  # type: ignore[override]
    deviceInfo: dict[str, Any]
    """Information about the newly connected device."""


class DeviceDidDisconnect(EventBase, DeviceSpecificEventMixin):
    event: Literal["deviceDidDisconnect"]  # type: ignore[override]
