from __future__ import annotations

from typing import Any, Literal

from streamdeck.models.events.base import EventBase
from streamdeck.models.events.common import ContextualEventMixin, DeviceSpecificEventMixin


class DidReceiveSettings(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    """Occurs when the settings associated with an action instance are requested, or when the the settings were updated by the property inspector."""
    event: Literal["didReceiveSettings"]  # type: ignore[override]
    payload: dict[str, Any]


class DidReceiveGlobalSettings(EventBase):
    """Occurs when the plugin receives the global settings from the Stream Deck."""
    event: Literal["didReceiveGlobalSettings"]  # type: ignore[override]
    payload: dict[Literal["settings"], dict[str, Any]]
