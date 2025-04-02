from __future__ import annotations

from typing import Any, Literal

from streamdeck.models.events.base import EventBase
from streamdeck.models.events.common import ContextualEventMixin, DeviceSpecificEventMixin


class WillAppear(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    event: Literal["willAppear"]  # type: ignore[override]
    payload: dict[str, Any]


class WillDisappear(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    event: Literal["willDisappear"]  # type: ignore[override]
    payload: dict[str, Any]
