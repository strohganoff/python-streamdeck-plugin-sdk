from __future__ import annotations

from typing import Any, Literal

from typing_extensions import TypedDict

from streamdeck.models.events.base import EventBase
from streamdeck.models.events.common import DeviceSpecificEventMixin


class TitleParametersDict(TypedDict):
    fontFamily: str
    fontSize: int
    fontStyle: str
    fontUnderline: bool
    showTitle: bool
    titleAlignment: Literal["top", "middle", "bottom"]
    titleColor: str


class TitleParametersDidChangePayload(TypedDict):
    controller: Literal["Keypad", "Encoder"]
    coordinates: dict[Literal["column", "row"], int]
    settings: dict[str, Any]
    state: int
    title: str
    titleParameters: TitleParametersDict


class TitleParametersDidChange(EventBase, DeviceSpecificEventMixin):
    event: Literal["titleParametersDidChange"]  # type: ignore[override]
    context: str
    """Identifies the instance of an action that caused the event, i.e. the specific key or dial."""
    payload: TitleParametersDidChangePayload
