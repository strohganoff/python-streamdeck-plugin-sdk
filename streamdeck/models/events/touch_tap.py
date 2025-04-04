from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from streamdeck.models.events.base import EventBase
from streamdeck.models.events.common import (
    BasePayload,
    ContextualEventMixin,
    CoordinatesPayloadMixin,
    DeviceSpecificEventMixin,
    EncoderControllerType,
)


class TouchTapPayload(BasePayload[EncoderControllerType], CoordinatesPayloadMixin):
    """Contextualized information for a TouchTap event."""
    hold: bool
    """Determines whether the tap was considered 'held'."""
    tap_position: Annotated[tuple[int, int], Field(alias="tapPos")]
    """Coordinates of where the touchscreen tap occurred, relative to the canvas of the action."""


class TouchTap(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    """Occurs when the user taps the touchscreen (Stream Deck +)."""
    event: Literal["touchTap"]  # type: ignore[override]
    payload: TouchTapPayload
    """Contextualized information for this event."""
