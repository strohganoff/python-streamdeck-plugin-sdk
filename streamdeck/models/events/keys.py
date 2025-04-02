from __future__ import annotations

from typing import Any, Literal

from streamdeck.models.events.base import EventBase
from streamdeck.models.events.common import ContextualEventMixin, DeviceSpecificEventMixin


class KeyDown(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    event: Literal["keyDown"]  # type: ignore[override]
    payload: dict[str, Any]


class KeyUp(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    event: Literal["keyUp"]  # type: ignore[override]
    payload: dict[str, Any]
