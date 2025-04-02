from __future__ import annotations

from typing import Any, Literal

from streamdeck.models.events.base import EventBase
from streamdeck.models.events.common import ContextualEventMixin, DeviceSpecificEventMixin


class TouchTap(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    """Occurs when the user taps the touchscreen (Stream Deck +)."""
    event: Literal["touchTap"]  # type: ignore[override]
    payload: dict[str, Any]
    """Contextualized information for this event."""
