from __future__ import annotations

from typing import Literal

from streamdeck.models.events.base import EventBase
from streamdeck.models.events.common import (
    ActionInstancePayloadEventMixin,
    BasePayload,
    CoordinatesPayloadMixin,
    DeviceSpecificEventMixin,
    EncoderControllerType,
)


## Payload models used in the below DialDown, DialRotate, and DialUp events


class EncoderPayload(BasePayload[EncoderControllerType], CoordinatesPayloadMixin):
    """Action-instance event data for a DialDown or DialUp event."""


class DialRotatePayload(EncoderPayload):
    """Action-instance event data for a DialRotate event."""

    pressed: bool
    """Determines whether the dial was pressed whilst the rotation occurred."""
    ticks: int
    """Number of ticks the dial was rotated; this can be a positive (clockwise) or negative (counter-clockwise) number."""


## Event models for DialDown, DialRotate, and DialUp events


class DialDown(EventBase[Literal["dialDown"]], ActionInstancePayloadEventMixin[EncoderPayload], DeviceSpecificEventMixin):  # fmt: skip
    """Occurs when the user presses a dial (Stream Deck +)."""

    payload: EncoderPayload
    """Action-instance event data for this event."""


class DialRotate(EventBase[Literal["dialRotate"]], ActionInstancePayloadEventMixin[DialRotatePayload], DeviceSpecificEventMixin):  # fmt: skip
    """Occurs when the user rotates a dial (Stream Deck +)."""

    payload: DialRotatePayload
    """Action-instance event data for this event."""


class DialUp(EventBase[Literal["dialUp"]], ActionInstancePayloadEventMixin[EncoderPayload], DeviceSpecificEventMixin):  # fmt: skip
    """Occurs when the user releases a pressed dial (Stream Deck +)."""

    payload: EncoderPayload
    """Action-instance event data for this event."""
