from __future__ import annotations

from typing import Literal

from streamdeck.models.events.base import EventBase
from streamdeck.models.events.common import (
    ActionInstanceEventMixin,
    DeviceSpecificEventMixin,
)
from streamdeck.types import PluginDefinedData  # noqa: TC001


class DidReceivePropertyInspectorMessage(EventBase[Literal["sendToPlugin"]], ActionInstanceEventMixin):
    """Occurs when a message was received from the UI."""

    payload: PluginDefinedData
    """The data payload received from the UI."""


class PropertyInspectorDidAppear(
    EventBase[Literal["propertyInspectorDidAppear"]],
    ActionInstanceEventMixin,
    DeviceSpecificEventMixin,
):
    """Occurs when the property inspector associated with the action becomes visible.

    I.e. the user selected an action in the Stream Deck application.
    """


class PropertyInspectorDidDisappear(EventBase[Literal["propertyInspectorDidDisappear"]], ActionInstanceEventMixin, DeviceSpecificEventMixin):  # fmt: skip
    """Occurs when the property inspector associated with the action becomes invisible.

    I.e. the user unselected the action in the Stream Deck application.
    """
