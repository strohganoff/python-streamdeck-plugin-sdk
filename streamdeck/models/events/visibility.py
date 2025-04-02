from __future__ import annotations

from typing import Any, Literal

from streamdeck.models.events.base import EventBase
from streamdeck.models.events.common import ContextualEventMixin, DeviceSpecificEventMixin


class WillAppear(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    """Occurs when an action appears on the Stream Deck due to the user navigating to another page, profile, folder, etc.

    This also occurs during startup if the action is on the "front page".
    An action refers to all types of actions, e.g. keys, dials, touchscreens, pedals, etc.
    """
    event: Literal["willAppear"]  # type: ignore[override]
    payload: dict[str, Any]


class WillDisappear(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    """Occurs when an action disappears from the Stream Deck due to the user navigating to another page, profile, folder, etc.

    An action refers to all types of actions, e.g. keys, dials, touchscreens, pedals, etc.
    """
    event: Literal["willDisappear"]  # type: ignore[override]
    payload: dict[str, Any]
