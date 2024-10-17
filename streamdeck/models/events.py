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

    @classmethod
    def is_action_specific(cls):
        return "context" in cls.model_fields


class ApplicationDidLaunchEvent(EventBase):
    event: Literal["applicationDidLaunch"]
    payload: dict[Literal["application"], str]
    """Payload containing the name of the application that triggered the event."""


class ApplicationDidTerminateEvent(EventBase):
    event: Literal["applicationDidTerminate"]
    payload: dict[Literal["application"], str]
    """Payload containing the name of the application that triggered the event."""


class DeviceDidConnectEvent(EventBase):
    event: Literal["deviceDidConnect"]
    device: str
    """Unique identifier of the Stream Deck device that this event is associated with."""
    deviceInfo: dict[str, Any]
    """Information about the newly connected device."""


class DeviceDidDisconnectEvent(EventBase):
    event: Literal["deviceDidDisconnect"]
    device: str
    """Unique identifier of the Stream Deck device that this event is associated with."""


class DialDownEvent(EventBase):
    event: Literal["dialDown"]
    context: str
    """Identifies the instance of an action that caused the event, i.e. the specific key or dial."""
    device: str
    """Unique identifier of the Stream Deck device that this event is associated with."""
    action: str
    """Unique identifier of the action"""
    payload: dict[str, Any]


class DialRotateEvent(EventBase):
    event: Literal["dialRotate"]
    context: str
    """Identifies the instance of an action that caused the event, i.e. the specific key or dial."""
    device: str
    """Unique identifier of the Stream Deck device that this event is associated with."""
    action: str
    """Unique identifier of the action"""
    payload: dict[str, Any]


class DialUpEvent(EventBase):
    event: Literal["dialUp"]
    context: str
    """Identifies the instance of an action that caused the event, i.e. the specific key or dial."""
    device: str
    """Unique identifier of the Stream Deck device that this event is associated with."""
    action: str
    """Unique identifier of the action"""
    payload: dict[str, Any]


class DidReceiveDeepLinkEvent(EventBase):
    event: Literal["didReceiveDeepLink"]
    payload: dict[Literal["url"], str]


class DidReceiveGlobalSettingsEvent(EventBase):
    event: Literal["didReceiveGlobalSettings"]
    payload: dict[Literal["settings"], dict[str, Any]]


class DidReceivePropertyInspectorMessageEvent(EventBase):
    event: Literal["sendToPlugin"]
    context: str
    """Identifies the instance of an action that caused the event, i.e. the specific key or dial."""
    action: str
    """Unique identifier of the action"""
    payload: dict[str, Any]


class DidReceiveSettingsEvent(EventBase):
    event: Literal["didReceiveSettings"]
    context: str
    """UUID of the instance of an action that caused the event."""
    device: str
    """UUID of the Stream Deck device that this event is associated with."""
    action: str
    """UUID of the action."""
    payload: dict[str, Any]


class KeyDownEvent(EventBase):
    event: Literal["keyDown"]
    context: str
    """Identifies the instance of an action that caused the event, i.e. the specific key or dial."""
    device: str
    """Unique identifier of the Stream Deck device that this event is associated with."""
    action: str
    """Unique identifier of the action"""
    payload: dict[str, Any]


class KeyUpEvent(EventBase):
    event: Literal["keyUp"]
    context: str
    """Identifies the instance of an action that caused the event, i.e. the specific key or dial."""
    device: str
    """Unique identifier of the Stream Deck device that this event is associated with."""
    action: str
    """Unique identifier of the action"""
    payload: dict[str, Any]


class PropertyInspectorDidAppearEvent(EventBase):
    event: Literal["propertyInspectorDidAppear"]
    context: str
    """Identifies the instance of an action that caused the event, i.e. the specific key or dial."""
    device: str
    """Unique identifier of the Stream Deck device that this event is associated with."""
    action: str
    """Unique identifier of the action"""


class PropertyInspectorDidDisappearEvent(EventBase):
    event: Literal["propertyInspectorDidDisappear"]
    context: str
    """Identifies the instance of an action that caused the event, i.e. the specific key or dial."""
    device: str
    """Unique identifier of the Stream Deck device that this event is associated with."""
    action: str
    """Unique identifier of the action"""


class SystemDidWakeUpEvent(EventBase):
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


class TitleParametersDidChangeEvent(EventBase):
    event: Literal["titleParametersDidChange"]
    context: str
    """Identifies the instance of an action that caused the event, i.e. the specific key or dial."""
    device: str
    """Unique identifier of the Stream Deck device that this event is associated with."""
    # payload: dict[str, Any]
    payload: TitleParametersDidChangePayload


class TouchTap(EventBase):
    event: Literal["touchTap"]
    context: str
    """Identifies the instance of an action that caused the event, i.e. the specific key or dial."""
    device: str
    """Unique identifier of the Stream Deck device that this event is associated with."""
    action: str
    """Unique identifier of the action"""
    payload: dict[str, Any]


class WillAppearEvent(EventBase):
    event: Literal["willAppear"]
    context: str
    """Identifies the instance of an action that caused the event, i.e. the specific key or dial."""
    device: str
    """Unique identifier of the Stream Deck device that this event is associated with."""
    action: str
    """Unique identifier of the action"""
    payload: dict[str, Any]


class WillDisappearEvent(EventBase):
    event: Literal["willDisappear"]
    context: str
    """Identifies the instance of an action that caused the event, i.e. the specific key or dial."""
    device: str
    """Unique identifier of the Stream Deck device that this event is associated with."""
    action: str
    """Unique identifier of the action"""
    payload: dict[str, Any]




event_adapter: TypeAdapter[EventBase] = TypeAdapter(
    Annotated[
        Union[  # noqa: UP007
            ApplicationDidLaunchEvent,
            ApplicationDidTerminateEvent,
            DeviceDidConnectEvent,
            DeviceDidDisconnectEvent,
            DialDownEvent,
            DialRotateEvent,
            DialUpEvent,
            DidReceiveDeepLinkEvent,
            KeyUpEvent,
            KeyDownEvent,
            DidReceivePropertyInspectorMessageEvent,
            PropertyInspectorDidAppearEvent,
            PropertyInspectorDidDisappearEvent,
            DidReceiveGlobalSettingsEvent,
            DidReceiveSettingsEvent,
            SystemDidWakeUpEvent,
            TitleParametersDidChangeEvent,
            TouchTap,
            WillAppearEvent,
            WillDisappearEvent,
        ],
        Field(discriminator="event")
    ]
)
