from __future__ import annotations

from typing import Annotated

from pydantic import Field

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


## Payload models used in the below KeyDown and KeyUp events

# It seems like for keyDown and keyUp events, the "controller" field is probably always missing, despite being defined in the official documentation.
OptionalKeyControllerTypeField = Annotated[KeypadControllerType, Field(default=None)]


class SingleActionKeyGesturePayload(
    BasePayload[OptionalKeyControllerTypeField],
    SingleActionPayloadMixin,
    StatefulActionPayloadMixin,
    CoordinatesPayloadMixin,
):
    """Contextualized information for a KeyDown or KeyUp event that is not part of a multi-action."""


class MultiActionKeyGesturePayload(
    BasePayload[OptionalKeyControllerTypeField],
    MultiActionPayloadMixin,
    StatefulActionPayloadMixin,
):
    """Contextualized information for a KeyDown or KeyUp event that is part of a multi-action."""
    user_desired_state: Annotated[int, Field(alias="userDesiredState")]
    """Desired state as specified by the user.

    Only applicable to actions that have multiple states defined within the manifest.json file, and when this action instance is part of a multi-action.
    """


## Event models for KeyDown and KeyUp events

class KeyDown(EventBase["keyDown"], ContextualEventMixin, DeviceSpecificEventMixin):
    """Occurs when the user presses a action down."""
    payload: CardinalityDiscriminated[SingleActionKeyGesturePayload, MultiActionKeyGesturePayload]
    """Contextualized information for this event."""


class KeyUp(EventBase["keyUp"], ContextualEventMixin, DeviceSpecificEventMixin):
    """Occurs when the user releases a pressed action."""
    payload: CardinalityDiscriminated[SingleActionKeyGesturePayload, MultiActionKeyGesturePayload]
    """Contextualized information for this event."""
