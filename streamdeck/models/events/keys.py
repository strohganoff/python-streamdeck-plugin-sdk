from __future__ import annotations

from typing import Annotated, Literal, Optional, Union

from pydantic import Field

from streamdeck.models.events.base import ConfiguredBaseModel, EventBase
from streamdeck.models.events.common import (
    CardinalityDiscriminated,
    ContextualEventMixin,
    CoordinatesPayloadMixin,
    DeviceSpecificEventMixin,
    MultiActionPayloadMixin,
    SingleActionPayloadMixin,
)


## Payload models used in the below KeyDown and KeyUp events

class SingleActionKeyGesturePayload(ConfiguredBaseModel, SingleActionPayloadMixin, CoordinatesPayloadMixin):
    """Contextualized information for a KeyDown or KeyUp event that is not part of a multi-action."""
    controller: Optional[Literal["Keypad"]] = None  # noqa: UP007
    """The 'Keypad' controller type refers to a standard action on a Stream Deck device, e.g. buttons or a pedal."""
    state: Optional[int] = None  # noqa: UP007
    """Current state of the action; only applicable to actions that have multiple states defined within the manifest.json file."""
    settings: PluginDefinedData
    """Settings associated with the action instance."""


class MultiActionKeyGesturePayload(ConfiguredBaseModel, MultiActionPayloadMixin):
    """Contextualized information for a KeyDown or KeyUp event that is part of a multi-action."""
    controller: Optional[Literal["Keypad"]] = None  # noqa: UP007
    """The 'Keypad' controller type refers to a standard action on a Stream Deck device, e.g. buttons or a pedal."""
    state: Optional[int] = None  # noqa: UP007
    """Current state of the action; only applicable to actions that have multiple states defined within the manifest.json file."""
    user_desired_state: Annotated[int, Field(alias="userDesiredState")]
    """Desired state as specified by the user.

    Only applicable to actions that have multiple states defined within the manifest.json file, and when this action instance is part of a multi-action.
    """
    settings: PluginDefinedData


## Event models for KeyDown and KeyUp events

class KeyDown(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    """Occurs when the user presses a action down."""
    event: Literal["keyDown"]  # type: ignore[override]
    payload: CardinalityDiscriminated[SingleActionKeyGesturePayload, MultiActionKeyGesturePayload]
    """Contextualized information for this event."""


class KeyUp(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    """Occurs when the user releases a pressed action."""
    event: Literal["keyUp"]  # type: ignore[override]
    payload: CardinalityDiscriminated[SingleActionKeyGesturePayload, MultiActionKeyGesturePayload]
    """Contextualized information for this event."""
