from __future__ import annotations

from typing import Any, Literal

from streamdeck.models.events.base import EventBase
from streamdeck.models.events.common import ContextualEventMixin, DeviceSpecificEventMixin


class DidReceivePropertyInspectorMessage(EventBase, ContextualEventMixin):
    event: Literal["sendToPlugin"]  # type: ignore[override]
    payload: dict[str, Any]


class PropertyInspectorDidAppear(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    event: Literal["propertyInspectorDidAppear"]  # type: ignore[override]


class PropertyInspectorDidDisappear(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    event: Literal["propertyInspectorDidDisappear"]  # type: ignore[override]
