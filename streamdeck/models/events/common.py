from __future__ import annotations

from typing import Any, Literal, Optional

from streamdeck.models.events.base import ConfiguredBaseModel


## Mixin classes for common event model fields.

class ContextualEventMixin:
    """Mixin class for event models that have action and context fields."""
    action: str
    """Unique identifier of the action"""
    context: str
    """Identifies the instance of an action that caused the event, i.e. the specific key or dial."""


class DeviceSpecificEventMixin:
    """Mixin class for event models that have a device field."""
    device: str
    """Unique identifier of the Stream Deck device that this event is associated with."""


## Payload models and metadata used by multiple event models.

PluginDefinedData = dict[str, Any]
"""Data of arbitrary structure that is defined in and relevant to the plugin."""


class CoordinatesDict(TypedDict):
    """Coordinates that identify the location of an action."""

    column: int
    """Column the action instance is located in, indexed from 0."""
    row: int
    """Row the action instance is located on, indexed from 0.

    When the device is DeviceType.StreamDeckPlus the row can be 0 for keys (Keypad),
    and will always be 0 for dials (Encoder).
    """


class Coordinates(NamedTuple):
    """Coordinates that identify the location of an action."""

    column: int
    """Column the action instance is located in, indexed from 0."""
    row: int
    """Row the action instance is located on, indexed from 0.

    When the device is DeviceType.StreamDeckPlus the row can be 0 for keys (Keypad),
    and will always be 0 for dials (Encoder).
    """


class CoordinatesPayloadMixin:
    """Mixin class for event models that have a coordinates field."""
    coordinates_obj: Annotated[
        CoordinatesDict, Field(alias="coordinates", repr=False)
    ]
    """Coordinates dictionary that identify the location of the action instance on the device."""

    @property
    def coordinates(self) -> Coordinates:
        """Coordinates that identify the location of the action instance on the device."""
        return Coordinates(**self.coordinates_obj)


class SingleActionPayload(ConfiguredBaseModel, CoordinatesPayloadMixin):
    """Contextualized information for a willAppear, willDisappear, and didReceiveSettings events that are not part of a multi-action."""
    controller: Literal["Encoder", "Keypad"]
    """Defines the controller type the action is applicable to.

    'Keypad' refers to a standard action on a Stream Deck device, e.g. buttons or a pedal.
    'Encoder' refers to a dial / touchscreen.
    """
    isInMultiAction: Literal[False]
    """Indicates that this event is not part of a multi-action."""
    state: Optional[int] = None  # noqa: UP007
    """Current state of the action; only applicable to actions that have multiple states defined within the manifest.json file."""
    settings: PluginDefinedData
    """Settings associated with the action instance."""


class MultiActionPayload(ConfiguredBaseModel):
    """Contextualized information for a willAppear, willDisappear, and didReceiveSettings events that are part of a multi-action.

    NOTE: Action instances that are part of a multi-action are only applicable to the 'Keypad' controller type.
    """
    controller: Literal["Keypad"]
    """The 'Keypad' controller type refers to a standard action on a Stream Deck device, e.g. buttons or a pedal.

    Action instances that are part of a multi-action are only applicable to the 'Keypad' controller type.
    """
    isInMultiAction: Literal[True]
    """Indicates that this event is part of a multi-action."""
    state: Optional[int] = None  # noqa: UP007
    """Current state of the action; only applicable to actions that have multiple states defined within the manifest.json file."""
    settings: PluginDefinedData
    """Settings associated with the action instance."""



