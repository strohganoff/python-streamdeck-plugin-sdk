from __future__ import annotations

from typing import Annotated, Literal, Optional, Union

from pydantic import Field

from streamdeck.models.events.base import ConfiguredBaseModel, EventBase
from streamdeck.models.events.common import ContextualEventMixin, DeviceSpecificEventMixin, PluginDefinedData


## Payload models used in the below KeyDown and KeyUp events

class SingleActionKeyGesturePayload(ConfiguredBaseModel):
    """Contextualized information for a KeyDown or KeyUp event that is not part of a multi-action."""
    controller: Optional[Literal["Keypad"]] = None  # noqa: UP007
    """The 'Keypad' controller type refers to a standard action on a Stream Deck device, e.g. buttons or a pedal."""
    coordinates: dict[Literal["column", "row"], int]
    """Coordinates that identify the location of the action instance on the device."""
    is_in_multi_action: Annotated[Literal[False], Field(alias="isInMultiAction")]
    """Indicates that this event is not part of a multi-action."""
    state: Optional[int] = None  # noqa: UP007
    """Current state of the action; only applicable to actions that have multiple states defined within the manifest.json file."""
    settings: PluginDefinedData
    """Settings associated with the action instance."""


class MultiActionKeyGesturePayload(ConfiguredBaseModel):
    """Contextualized information for a KeyDown or KeyUp event that is part of a multi-action."""
    controller: Optional[Literal["Keypad"]] = None  # noqa: UP007
    """The 'Keypad' controller type refers to a standard action on a Stream Deck device, e.g. buttons or a pedal."""
    is_in_multi_action: Annotated[Literal[True], Field(alias="isInMultiAction")]
    """Indicates that this event is part of a multi-action."""
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
    payload: Annotated[Union[SingleActionKeyGesturePayload, MultiActionKeyGesturePayload], Field(discriminator="isInMultiAction")]  # noqa: UP007
    """Contextualized information for this event."""


class KeyUp(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    """Occurs when the user releases a pressed action."""
    event: Literal["keyUp"]  # type: ignore[override]
    payload: Annotated[Union[SingleActionKeyGesturePayload, MultiActionKeyGesturePayload], Field(discriminator="is_in_multi_action")]  # noqa: UP007
    """Contextualized information for this event."""
