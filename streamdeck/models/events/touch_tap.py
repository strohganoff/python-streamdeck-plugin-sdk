from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from streamdeck.models.events.base import EventBase
from streamdeck.models.events.common import (
    ActionInstancePayloadEventMixin,
    BasePayload,
    CoordinatesPayloadMixin,
    DeviceSpecificEventMixin,
    EncoderControllerType,
)


class TouchTapPayload(BasePayload[EncoderControllerType], CoordinatesPayloadMixin):
    """Action-instance event data for a TouchTap event."""

    hold: bool
    """Determines whether the tap was considered 'held'."""
    tap_position: Annotated[tuple[int, int], Field(alias="tapPos")]
    """Coordinates of where the touchscreen tap occurred, relative to the canvas of the action."""


class TouchTap(EventBase[Literal["touchTap"]], ActionInstancePayloadEventMixin[TouchTapPayload], DeviceSpecificEventMixin):  # fmt: skip
    """Occurs when the user taps the touchscreen (Stream Deck +)."""

    payload: TouchTapPayload
    """Action-instance event data for this event."""
