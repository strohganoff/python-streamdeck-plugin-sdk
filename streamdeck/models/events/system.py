from __future__ import annotations

from streamdeck.models.events.base import EventBase


class SystemDidWakeUp(EventBase["systemDidWakeUp"]):
    """Occurs when the computer wakes up."""
