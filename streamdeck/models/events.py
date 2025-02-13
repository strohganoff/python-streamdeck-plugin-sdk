from __future__ import annotations

from abc import ABC
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter
from typing_extensions import TypedDict


# TODO: Create more explicitly-defined payload objects.


class EventBase(BaseModel, ABC):
    model_config = ConfigDict(use_attribute_docstrings=True)

    event: str
    """Name of the event used to identify what occurred."""


class ContextualEventMixin:
    action: str
    """Unique identifier of the action"""
    context: str
    """Identifies the instance of an action that caused the event, i.e. the specific key or dial."""

class DeviceSpecificEventMixin:
    device: str
    """Unique identifier of the Stream Deck device that this event is associated with."""


class ApplicationDidLaunch(EventBase):
    event: Literal["applicationDidLaunch"]
    payload: dict[Literal["application"], str]
    """Payload containing the name of the application that triggered the event."""


class ApplicationDidTerminate(EventBase):
    event: Literal["applicationDidTerminate"]
    payload: dict[Literal["application"], str]
    """Payload containing the name of the application that triggered the event."""


class DeviceDidConnect(EventBase, DeviceSpecificEventMixin):
    event: Literal["deviceDidConnect"]
    deviceInfo: dict[str, Any]
    """Information about the newly connected device."""


class DeviceDidDisconnect(EventBase, DeviceSpecificEventMixin):
    event: Literal["deviceDidDisconnect"]


class DialDown(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    event: Literal["dialDown"]
    payload: dict[str, Any]


class DialRotate(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    event: Literal["dialRotate"]
    payload: dict[str, Any]


class DialUp(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    event: Literal["dialUp"]
    payload: dict[str, Any]


class DidReceiveDeepLink(EventBase):
    event: Literal["didReceiveDeepLink"]
    payload: dict[Literal["url"], str]


class DidReceiveGlobalSettings(EventBase):
    event: Literal["didReceiveGlobalSettings"]
    payload: dict[Literal["settings"], dict[str, Any]]


class DidReceivePropertyInspectorMessage(EventBase, ContextualEventMixin):
    event: Literal["sendToPlugin"]
    payload: dict[str, Any]


class DidReceiveSettings(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    event: Literal["didReceiveSettings"]
    payload: dict[str, Any]


class KeyDown(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    event: Literal["keyDown"]
    payload: dict[str, Any]


class KeyUp(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    event: Literal["keyUp"]
    payload: dict[str, Any]


class PropertyInspectorDidAppear(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    event: Literal["propertyInspectorDidAppear"]


class PropertyInspectorDidDisappear(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    event: Literal["propertyInspectorDidDisappear"]


class SystemDidWakeUp(EventBase):
    event: Literal["systemDidWakeUp"]


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
    event: Literal["titleParametersDidChange"]
    context: str
    """Identifies the instance of an action that caused the event, i.e. the specific key or dial."""
    payload: TitleParametersDidChangePayload


class TouchTap(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    event: Literal["touchTap"]
    payload: dict[str, Any]


class WillAppear(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    event: Literal["willAppear"]
    payload: dict[str, Any]


class WillDisappear(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    event: Literal["willDisappear"]
    payload: dict[str, Any]




event_adapter: TypeAdapter[EventBase] = TypeAdapter(
    Annotated[
        Union[  # noqa: UP007
            ApplicationDidLaunch,
            ApplicationDidTerminate,
            DeviceDidConnect,
            DeviceDidDisconnect,
            DialDown,
            DialRotate,
            DialUp,
            DidReceiveDeepLink,
            KeyUp,
            KeyDown,
            DidReceivePropertyInspectorMessage,
            PropertyInspectorDidAppear,
            PropertyInspectorDidDisappear,
            DidReceiveGlobalSettings,
            DidReceiveSettings,
            SystemDidWakeUp,
            TitleParametersDidChange,
            TouchTap,
            WillAppear,
            WillDisappear,
        ],
        Field(discriminator="event")
    ]
)
