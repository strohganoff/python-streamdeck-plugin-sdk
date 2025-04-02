from __future__ import annotations

from typing import Any, Literal

from streamdeck.models.events.base import EventBase
from streamdeck.models.events.common import ContextualEventMixin, DeviceSpecificEventMixin


class DidReceiveSettings(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    event: Literal["didReceiveSettings"]  # type: ignore[override]
    payload: dict[str, Any]


class DidReceiveGlobalSettings(EventBase):
    event: Literal["didReceiveGlobalSettings"]  # type: ignore[override]
    payload: dict[Literal["settings"], dict[str, Any]]
