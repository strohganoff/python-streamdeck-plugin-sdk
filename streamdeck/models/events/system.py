from __future__ import annotations

from typing import Literal

from streamdeck.models.events.base import EventBase


class SystemDidWakeUp(EventBase[Literal["systemDidWakeUp"]]):
    """Occurs when the computer wakes up."""
