from __future__ import annotations

from typing import Any, Literal

from streamdeck.models.events.base import EventBase
from streamdeck.models.events.common import ContextualEventMixin, DeviceSpecificEventMixin


class KeyDown(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    """Occurs when the user presses a action down."""
    event: Literal["keyDown"]  # type: ignore[override]
    payload: dict[str, Any]
    """Contextualized information for this event."""


class KeyUp(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    """Occurs when the user releases a pressed action."""
    event: Literal["keyUp"]  # type: ignore[override]
    payload: dict[str, Any]
    """Contextualized information for this event."""
