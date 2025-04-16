from __future__ import annotations

from typing import Literal

from streamdeck.models.events.base import (
    EventBase,
)
from streamdeck.models.events.common import (
    ContextualEventMixin,
    DeviceSpecificEventMixin,
    PluginDefinedData,
)


class DidReceivePropertyInspectorMessage(EventBase[Literal["sendToPlugin"]], ContextualEventMixin):
    """Occurs when a message was received from the UI."""
    payload: PluginDefinedData
    """The data payload received from the UI."""


class PropertyInspectorDidAppear(EventBase[Literal["propertyInspectorDidAppear"]], ContextualEventMixin, DeviceSpecificEventMixin):
    """Occurs when the property inspector associated with the action becomes visible.

    I.e. the user selected an action in the Stream Deck application.
    """


class PropertyInspectorDidDisappear(EventBase[Literal["propertyInspectorDidDisappear"]], ContextualEventMixin, DeviceSpecificEventMixin):
    """Occurs when the property inspector associated with the action becomes invisible.

    I.e. the user unselected the action in the Stream Deck application.
    """
