from __future__ import annotations

from typing import Any, Literal

from streamdeck.models.events.base import EventBase
from streamdeck.models.events.common import ContextualEventMixin, DeviceSpecificEventMixin


class DialDown(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    event: Literal["dialDown"]  # type: ignore[override]
    payload: dict[str, Any]


class DialRotate(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    event: Literal["dialRotate"]  # type: ignore[override]
    payload: dict[str, Any]


class DialUp(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    event: Literal["dialUp"]  # type: ignore[override]
    payload: dict[str, Any]
