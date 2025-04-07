from __future__ import annotations

from typing import Literal

from streamdeck.models.events.base import EventBase
from streamdeck.models.events.common import (
    ContextualEventMixin,
    DeviceSpecificEventMixin,
    PluginDefinedData,
)


class DidReceivePropertyInspectorMessage(EventBase, ContextualEventMixin):
    """Occurs when a message was received from the UI."""
    event: Literal["sendToPlugin"]  # type: ignore[override]
    payload: PluginDefinedData
    """The data payload received from the UI."""


class PropertyInspectorDidAppear(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    """Occurs when the property inspector associated with the action becomes visible.

    I.e. the user selected an action in the Stream Deck application.
    """
    event: Literal["propertyInspectorDidAppear"]  # type: ignore[override]


class PropertyInspectorDidDisappear(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    """Occurs when the property inspector associated with the action becomes invisible.

    I.e. the user unselected the action in the Stream Deck application.
    """
    event: Literal["propertyInspectorDidDisappear"]  # type: ignore[override]
