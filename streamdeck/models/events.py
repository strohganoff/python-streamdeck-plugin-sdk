from __future__ import annotations

from abc import ABC
from typing import Annotated, Any, Final, Literal, Union, get_args, get_type_hints

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter
from typing_extensions import LiteralString, TypedDict, TypeIs  # noqa: UP035


# TODO: Create more explicitly-defined payload objects.


class EventBase(BaseModel, ABC):
    """Base class for event models that represent Stream Deck Plugin SDK events."""
    # Configure to use the docstrings of the fields as the field descriptions.
    model_config = ConfigDict(use_attribute_docstrings=True)

    event: str
    """Name of the event used to identify what occurred.

    Subclass models must define this field as a Literal type with the event name string that the model represents.
    """

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Validate that the event field is a Literal[str] type."""
        super().__init_subclass__(**kwargs)

        model_event_type = get_type_hints(cls)["event"]

        if not is_literal_str_type(model_event_type):
            msg = f"The event field annotation must be a Literal[str] type. Given type: {model_event_type}"
            raise TypeError(msg)

    @classmethod
    def get_model_event_name(cls) -> tuple[str, ...]:
        """Get the value of the subclass model's event field Literal annotation."""
        model_event_type = get_type_hints(cls)["event"]

        # Ensure that the event field annotation is a Literal type.
        if not is_literal_str_type(model_event_type):
            msg = "The `event` field annotation of an Event model must be a Literal[str] type."
            raise TypeError(msg)

        return get_args(model_event_type)


def is_literal_str_type(value: object | None) -> TypeIs[LiteralString]:
    """Check if a type is a Literal type."""
    if value is None:
        return False

    event_field_base_type = getattr(value, "__origin__", None)

    if event_field_base_type is not Literal:
        return False

    return all(isinstance(literal_value, str) for literal_value in get_args(value))


## Mixin classes for common event model fields.

class ContextualEventMixin:
    """Mixin class for event models that have action and context fields."""
    action: str
    """Unique identifier of the action"""
    context: str
    """Identifies the instance of an action that caused the event, i.e. the specific key or dial."""

class DeviceSpecificEventMixin:
    """Mixin class for event models that have a device field."""
    device: str
    """Unique identifier of the Stream Deck device that this event is associated with."""


## EventBase implementation models of the Stream Deck Plugin SDK events.

class ApplicationDidLaunch(EventBase):
    event: Literal["applicationDidLaunch"]  # type: ignore[override]
    payload: dict[Literal["application"], str]
    """Payload containing the name of the application that triggered the event."""


class ApplicationDidTerminate(EventBase):
    event: Literal["applicationDidTerminate"]  # type: ignore[override]
    payload: dict[Literal["application"], str]
    """Payload containing the name of the application that triggered the event."""


class DeviceDidConnect(EventBase, DeviceSpecificEventMixin):
    event: Literal["deviceDidConnect"]  # type: ignore[override]
    deviceInfo: dict[str, Any]
    """Information about the newly connected device."""


class DeviceDidDisconnect(EventBase, DeviceSpecificEventMixin):
    event: Literal["deviceDidDisconnect"]  # type: ignore[override]


class DialDown(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    event: Literal["dialDown"]  # type: ignore[override]
    payload: dict[str, Any]


class DialRotate(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    event: Literal["dialRotate"]  # type: ignore[override]
    payload: dict[str, Any]


class DialUp(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    event: Literal["dialUp"]  # type: ignore[override]
    payload: dict[str, Any]


class DidReceiveDeepLink(EventBase):
    event: Literal["didReceiveDeepLink"]  # type: ignore[override]
    payload: dict[Literal["url"], str]


class DidReceiveGlobalSettings(EventBase):
    event: Literal["didReceiveGlobalSettings"]  # type: ignore[override]
    payload: dict[Literal["settings"], dict[str, Any]]


class DidReceivePropertyInspectorMessage(EventBase, ContextualEventMixin):
    event: Literal["sendToPlugin"]  # type: ignore[override]
    payload: dict[str, Any]


class DidReceiveSettings(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    event: Literal["didReceiveSettings"]  # type: ignore[override]
    payload: dict[str, Any]


class KeyDown(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    event: Literal["keyDown"]  # type: ignore[override]
    payload: dict[str, Any]


class KeyUp(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    event: Literal["keyUp"]  # type: ignore[override]
    payload: dict[str, Any]


class PropertyInspectorDidAppear(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    event: Literal["propertyInspectorDidAppear"]  # type: ignore[override]


class PropertyInspectorDidDisappear(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    event: Literal["propertyInspectorDidDisappear"]  # type: ignore[override]


class SystemDidWakeUp(EventBase):
    event: Literal["systemDidWakeUp"]  # type: ignore[override]


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


class TouchTap(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    event: Literal["touchTap"]  # type: ignore[override]
    payload: dict[str, Any]


class WillAppear(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    event: Literal["willAppear"]  # type: ignore[override]
    payload: dict[str, Any]


class WillDisappear(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    event: Literal["willDisappear"]  # type: ignore[override]
    payload: dict[str, Any]


## Default event models and names.


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


DEFAULT_EVENT_MODELS: Final[list[type[EventBase]]] = [
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
]


def _get_default_event_names() -> set[str]:
    default_event_names: set[str] = set()

    for event_model in DEFAULT_EVENT_MODELS:
        default_event_names.update(event_model.get_model_event_name())

    return default_event_names


DEFAULT_EVENT_NAMES: Final[set[str]] = _get_default_event_names()
