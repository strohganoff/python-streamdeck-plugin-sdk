from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

from streamdeck.models.events.base import EventBase
from streamdeck.models.events.common import ContextualEventMixin, DeviceSpecificEventMixin


class TouchTapPayload(BaseModel):
    """Contextualized information for a TouchTap event."""
    controller: Literal["Encoder"]
    """The 'Encoder' controller type refers to a dial or touchscreen on a 'Stream Deck +' device."""
    coordinates: dict[Literal["column", "row"], int]
    """Coordinates that identify the location of the action instance on the device."""
    hold: bool
    """Determines whether the tap was considered 'held'."""
    tapPos: tuple[int, int]  # noqa: N815
    """Coordinates of where the touchscreen tap occurred, relative to the canvas of the action."""
    settings: dict[str, Any]
    """Settings associated with the action instance."""

class TouchTap(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    """Occurs when the user taps the touchscreen (Stream Deck +)."""
    event: Literal["touchTap"]  # type: ignore[override]
    payload: TouchTapPayload
    """Contextualized information for this event."""
