from __future__ import annotations

from typing import Literal

from streamdeck.models.events.base import EventBase


class SystemDidWakeUp(EventBase):
    """Occurs when the computer wakes up."""
    event: Literal["systemDidWakeUp"]  # type: ignore[override]
