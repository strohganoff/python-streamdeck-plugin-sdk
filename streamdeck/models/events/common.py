from __future__ import annotations

from abc import ABC
from typing import Annotated, Any, Generic, Literal, NamedTuple, Optional, Union

from pydantic import Field
from typing_extensions import TypedDict, TypeVar

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


EncoderControllerType = Literal["Encoder"]
"""The 'Encoder' controller type refers to a dial or touchscreen on a 'Stream Deck +' device."""
KeypadControllerType = Literal["Keypad"]
"""The 'Keypad' controller type refers to a standard action on a Stream Deck device, e.g. buttons or a pedal."""
ControllerType = Literal[EncoderControllerType, KeypadControllerType]
"""Defines the controller type the action is applicable to."""

CT = TypeVar("CT", bound=ControllerType, default=ControllerType)


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


class BasePayload(ConfiguredBaseModel, Generic[CT], ABC):
    """Base class for all complex payload models."""
    controller: CT
    """Defines the controller type the action is applicable to.

    'Keypad' refers to a standard action on a Stream Deck device, e.g. buttons or a pedal.
    'Encoder' refers to a dial / touchscreen on a 'Stream Deck +' device.
    """
    settings: PluginDefinedData
    """Settings associated with the action instance."""


class BaseActionPayload(BasePayload[CT], ABC):
    """Base class for payloads of action events."""

    state: Optional[int] = None  # noqa: UP007
    """Current state of the action.

    Only applicable to actions that have multiple states defined within the manifest.json file.
    """


class SingleActionPayloadMixin:
    """Mixin class for event models that have a single action payload."""

    is_in_multi_action: Annotated[Literal[False], Field(alias="isInMultiAction")]
    """Indicates that this event is not part of a multi-action."""


class MultiActionPayloadMixin:
    """Mixin class for event models that have a multi-action payload."""

    is_in_multi_action: Annotated[Literal[True], Field(alias="isInMultiAction")]
    """Indicates that this event is part of a multi-action."""


CardinalityDiscriminated = Annotated[
    Union[  # noqa: UP007
        TypeVar("S", bound=SingleActionPayloadMixin),
        TypeVar("M", bound=MultiActionPayloadMixin),
    ],
    Field(discriminator="is_in_multi_action"),
]
"""Generic type for a payload that either subclasses SingleActionPayloadMixin or MultiActionPayloadMixin—meaning it can be either a single action or a multi-action."""
