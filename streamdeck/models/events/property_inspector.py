from __future__ import annotations

from streamdeck.models.events.base import EventBase
from streamdeck.models.events.common import (
    ContextualEventMixin,
    DeviceSpecificEventMixin,
)
from streamdeck.types import PluginDefinedData  # noqa: TC001


class DidReceivePropertyInspectorMessage(EventBase["sendToPlugin"], ContextualEventMixin):
    """Occurs when a message was received from the UI."""
    payload: PluginDefinedData
    """The data payload received from the UI."""


class PropertyInspectorDidAppear(EventBase["propertyInspectorDidAppear"], ContextualEventMixin, DeviceSpecificEventMixin):
    """Occurs when the property inspector associated with the action becomes visible.

    I.e. the user selected an action in the Stream Deck application.
    """


class PropertyInspectorDidDisappear(EventBase["propertyInspectorDidDisappear"], ContextualEventMixin, DeviceSpecificEventMixin):
    """Occurs when the property inspector associated with the action becomes invisible.

    I.e. the user unselected the action in the Stream Deck application.
    """
