from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel


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


## Payload models used by multiple event models.

class SingleActionPayload(BaseModel):
    """Contextualized information for a willAppear, willDisappear, and didReceiveSettings events that are not part of a multi-action."""
    controller: Literal["Encoder", "Keypad"]
    """Defines the controller type the action is applicable to.

    'Keypad' refers to a standard action on a Stream Deck device, e.g. buttons or a pedal.
    'Encoder' refers to a dial / touchscreen.
    """
    coordinates: dict[Literal["column", "row"], int]
    """Coordinates that identify the location of the action instance on the device."""
    isInMultiAction: Literal[False]
    """Indicates that this event is not part of a multi-action."""
    state: Optional[int] = None  # noqa: UP007
    """Current state of the action; only applicable to actions that have multiple states defined within the manifest.json file."""
    settings: dict[str, Any]
    """Settings associated with the action instance."""


class MultiActionPayload(BaseModel):
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
    settings: dict[str, Any]
    """Settings associated with the action instance."""



