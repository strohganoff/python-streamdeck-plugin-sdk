from typing import Annotated, Final, Literal

from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from streamdeck.models.events.base import EventBase
from streamdeck.models.events.common import DeviceSpecificEventMixin


DeviceTypeId = Literal[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


DeviceType = Literal[
    "Stream Deck",
    "Stream Deck Mini",
    "Stream Deck XL",
    "Stream Deck Mobile",
    "Corsair GKeys",
    "Stream Deck Pedal",
    "Corsair Voyager",
    "Stream Deck +",
    "SCUF Controller",
    "Stream Deck Neo",
]


DEVICE_TYPE_BY_ID: Final[dict[DeviceTypeId, DeviceType]] = {
    0: "Stream Deck",
    1: "Stream Deck Mini",
    2: "Stream Deck XL",
    3: "Stream Deck Mobile",
    4: "Corsair GKeys",
    5: "Stream Deck Pedal",
    6: "Corsair Voyager",
    7: "Stream Deck +",
    8: "SCUF Controller",
    9: "Stream Deck Neo",
}


class DeviceSize(TypedDict):
    """Number of action slots, excluding dials / touchscreens, available to the device."""
    columns: int
    rows: int


class DeviceInfo(BaseModel):
    """Information about the newly connected device."""
    name: str
    """Name of the device, as specified by the user in the Stream Deck application."""
    size: DeviceSize
    """Number of action slots, excluding dials / touchscreens, available to the device."""
    _type: Annotated[DeviceTypeId, Field(alias="type")]
    """The type (id) of the device that was connected."""

    @property
    def type(self) -> DeviceType:
        """The type (product name) of the device that was connected."""
        if self._type not in DEVICE_TYPE_BY_ID:
            msg = f"Unknown device type id: {self._type}"
            raise ValueError(msg)

        return DEVICE_TYPE_BY_ID[self._type]


class DeviceDidConnect(EventBase, DeviceSpecificEventMixin):
    """Occurs when a Stream Deck device is connected."""
    event: Literal["deviceDidConnect"]  # type: ignore[override]
    deviceInfo: DeviceInfo
    """Information about the newly connected device."""


class DeviceDidDisconnect(EventBase, DeviceSpecificEventMixin):
    """Occurs when a Stream Deck device is disconnected."""
    event: Literal["deviceDidDisconnect"]  # type: ignore[override]
    device: str
    """Unique identifier of the Stream Deck device that this event is associated with."""
