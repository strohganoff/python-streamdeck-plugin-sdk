from typing import Annotated, Final, Literal, NamedTuple

from pydantic import Field
from typing_extensions import TypedDict

from streamdeck.models.events.base import ConfiguredBaseModel, EventBase
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


class DeviceSizeDict(TypedDict):
    """Number of action slots, excluding dials / touchscreens, available to the device."""
    columns: int
    rows: int


class DeviceSize(NamedTuple):
    """Number of action slots, excluding dials / touchscreens, available to the device."""
    columns: int
    rows: int


class DeviceInfo(ConfiguredBaseModel):
    """Information about the newly connected device."""
    name: str
    """Name of the device, as specified by the user in the Stream Deck application."""
    type_id: Annotated[DeviceTypeId, Field(alias="type", repr=False)]
    """The type (id) of the device that was connected."""
    size_obj: Annotated[DeviceSizeDict, Field(alias="size", repr=False)]
    """Number of action slots, excluding dials / touchscreens, available to the device."""

    @property
    def type(self) -> DeviceType:
        """The type (product name) of the device that was connected."""
        if self.type_id not in DEVICE_TYPE_BY_ID:
            msg = f"Unknown device type id: {self.type_id}"
            raise ValueError(msg)

        return DEVICE_TYPE_BY_ID[self.type_id]

    @property
    def size(self) -> DeviceSize:
        """Number of action slots, excluding dials / touchscreens, available to the device."""
        return DeviceSize(**self.size_obj)

    def __repr__(self) -> str:
        """Return a string representation of the device info."""
        return f"DeviceInfo(name={self.name}, type={self.type}, size={self.size})"


class DeviceDidConnect(EventBase, DeviceSpecificEventMixin):
    """Occurs when a Stream Deck device is connected."""
    event: Literal["deviceDidConnect"]  # type: ignore[override]
    device_info: Annotated[DeviceInfo, Field(alias="deviceInfo")]
    """Information about the newly connected device."""


class DeviceDidDisconnect(EventBase, DeviceSpecificEventMixin):
    """Occurs when a Stream Deck device is disconnected."""
    event: Literal["deviceDidDisconnect"]  # type: ignore[override]
