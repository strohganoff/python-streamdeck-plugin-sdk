from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from streamdeck.models.events.base import EventBase
from streamdeck.models.events.common import (
    ContextualEventMixin,
    DeviceSpecificEventMixin,
    PluginDefinedData,
)


class TouchTapPayload(ConfiguredBaseModel):
    """Contextualized information for a TouchTap event."""
    controller: Literal["Encoder"]
    """The 'Encoder' controller type refers to a dial or touchscreen on a 'Stream Deck +' device."""
    coordinates: dict[Literal["column", "row"], int]
    """Coordinates that identify the location of the action instance on the device."""
    hold: bool
    """Determines whether the tap was considered 'held'."""
    tap_position: Annotated[tuple[int, int], Field(alias="tapPos")]
    """Coordinates of where the touchscreen tap occurred, relative to the canvas of the action."""
    settings: PluginDefinedData

class TouchTap(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    """Occurs when the user taps the touchscreen (Stream Deck +)."""
    event: Literal["touchTap"]  # type: ignore[override]
    payload: TouchTapPayload
    """Contextualized information for this event."""
