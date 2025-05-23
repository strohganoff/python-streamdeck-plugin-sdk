from __future__ import annotations

from streamdeck.models.events.base import EventBase
from streamdeck.models.events.common import (
    BasePayload,
    CardinalityDiscriminated,
    ContextualEventMixin,
    CoordinatesPayloadMixin,
    DeviceSpecificEventMixin,
    KeypadControllerType,
    MultiActionPayloadMixin,
    SingleActionPayloadMixin,
    StatefulActionPayloadMixin,
)


class SingleActionVisibilityPayload(
    BasePayload,
    SingleActionPayloadMixin,
    StatefulActionPayloadMixin,
    CoordinatesPayloadMixin,
):
    """Contextualized information for willAppear and willDisappear events that is not part of a multi-action."""


class MultiActionVisibilityPayload(
    BasePayload[KeypadControllerType],
    MultiActionPayloadMixin,
    StatefulActionPayloadMixin,
):
    """Contextualized information for willAppear and willDisappear events that is part of a multi-action."""


## Event models for WillAppear and WillDisappear events

class WillAppear(EventBase["willAppear"], ContextualEventMixin, DeviceSpecificEventMixin):
    """Occurs when an action appears on the Stream Deck due to the user navigating to another page, profile, folder, etc.

    This also occurs during startup if the action is on the "front page".
    An action refers to all types of actions, e.g. keys, dials, touchscreens, pedals, etc.
    """
    payload: CardinalityDiscriminated[SingleActionVisibilityPayload, MultiActionVisibilityPayload]


class WillDisappear(EventBase["willDisappear"], ContextualEventMixin, DeviceSpecificEventMixin):
    """Occurs when an action disappears from the Stream Deck due to the user navigating to another page, profile, folder, etc.

    An action refers to all types of actions, e.g. keys, dials, touchscreens, pedals, etc.
    """
    payload: CardinalityDiscriminated[SingleActionVisibilityPayload, MultiActionVisibilityPayload]
