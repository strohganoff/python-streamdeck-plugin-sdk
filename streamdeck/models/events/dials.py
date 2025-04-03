from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

from streamdeck.models.events.base import EventBase
from streamdeck.models.events.common import ContextualEventMixin, DeviceSpecificEventMixin


## Payload models used in the below DialDown, DialRotate, and DialUp events

class EncoderPayload(BaseModel):
    """Contextualized information for a DialDown or DialUp event."""
    controller: Literal["Encoder"]
    """The 'Encoder' controller type refers to a dial or touchscreen on a 'Stream Deck +' device."""
    coordinates: dict[Literal["column", "row"], int]
    """Coordinates that identify the location of the action instance on the device."""
    settings: dict[str, Any]
    """Settings associated with the action instance."""


class DialRotatePayload(BaseModel):
    """Contextualized information for a DialRotate event."""
    controller: Literal["Encoder"]
    """The 'Encoder' controller type refers to a dial or touchscreen on a 'Stream Deck +' device."""
    coordinates: dict[Literal["column", "row"], int]
    """Coordinates that identify the location of the action instance on the device."""
    pressed: bool
    """Determines whether the dial was pressed whilst the rotation occurred."""
    ticks: int
    """Number of ticks the dial was rotated; this can be a positive (clockwise) or negative (counter-clockwise) number."""
    settings: dict[str, Any]
    """Settings associated with the action instance."""


## Event models for DialDown, DialRotate, and DialUp events

class DialDown(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    """Occurs when the user presses a dial (Stream Deck +)."""
    event: Literal["dialDown"]  # type: ignore[override]
    payload: EncoderPayload
    """Contextualized information for this event."""


class DialRotate(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    """Occurs when the user rotates a dial (Stream Deck +)."""
    event: Literal["dialRotate"]  # type: ignore[override]
    payload: DialRotatePayload
    """Contextualized information for this event."""


class DialUp(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    """Occurs when the user releases a pressed dial (Stream Deck +)."""
    event: Literal["dialUp"]  # type: ignore[override]
    payload: EncoderPayload
    """Contextualized information for this event."""
