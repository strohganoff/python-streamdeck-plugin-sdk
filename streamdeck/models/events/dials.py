from __future__ import annotations

from typing import Any, Literal

from streamdeck.models.events.base import EventBase
from streamdeck.models.events.common import ContextualEventMixin, DeviceSpecificEventMixin


class DialDown(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    """Occurs when the user presses a dial (Stream Deck +)."""
    event: Literal["dialDown"]  # type: ignore[override]
    payload: dict[str, Any]
    """Contextualized information for this event."""


class DialRotate(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    """Occurs when the user rotates a dial (Stream Deck +)."""
    event: Literal["dialRotate"]  # type: ignore[override]
    payload: dict[str, Any]
    """Contextualized information for this event."""


class DialUp(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    """Occurs when the user releases a pressed dial (Stream Deck +)."""
    event: Literal["dialUp"]  # type: ignore[override]
    payload: dict[str, Any]
    """Contextualized information for this event."""
