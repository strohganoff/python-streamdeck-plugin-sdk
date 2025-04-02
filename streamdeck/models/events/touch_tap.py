from __future__ import annotations

from typing import Any, Literal

from streamdeck.models.events.base import EventBase
from streamdeck.models.events.common import ContextualEventMixin, DeviceSpecificEventMixin


class TouchTap(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    event: Literal["touchTap"]  # type: ignore[override]
    payload: dict[str, Any]
