from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Literal, Protocol, TypeVar, Union

from typing_extensions import TypeAlias, TypeIs  # noqa: UP035

from streamdeck.models.events import EventBase


if TYPE_CHECKING:
    from streamdeck.command_sender import StreamDeckCommandSender


available_event_names: set[EventNameStr] = {
    "applicationDidLaunch",
    "applicationDidTerminate",
    "deviceDidConnect",
    "deviceDidDisconnect",
    "dialDown",
    "dialRotate",
    "dialUp",
    "didReceiveGlobalSettings",
    "didReceiveDeepLink",
    "didReceiveSettings",
    "sendToPlugin",  # DidReceivePropertyInspectorMessage event
    "keyDown",
    "keyUp",
    "propertyInspectorDidAppear",
    "propertyInspectorDidDisappear",
    "systemDidWakeUp",
    "titleParametersDidChange",
    "touchTap",
    "willAppear",
    "willDisappear",
}


# For backwards compatibility with older versions of Python, we can't just use available_event_names as the values of the Literal EventNameStr.
EventNameStr: TypeAlias = Literal[  # noqa: UP040
    "applicationDidLaunch",
    "applicationDidTerminate",
    "deviceDidConnect",
    "deviceDidDisconnect",
    "dialDown",
    "dialRotate",
    "dialUp",
    "didReceiveGlobalSettings",
    "didReceiveDeepLink",
    "didReceiveSettings",
    "sendToPlugin",  # DidReceivePropertyInspectorMessage event
    "keyDown",
    "keyUp",
    "propertyInspectorDidAppear",
    "propertyInspectorDidDisappear",
    "systemDidWakeUp",
    "titleParametersDidChange",
    "touchTap",
    "willAppear",
    "willDisappear"
]


def is_valid_event_name(event_name: str) -> TypeIs[EventNameStr]:
    """Check if the event name is one of the available event names."""
    return event_name in available_event_names


### Event Handler Type Definitions ###

## Protocols for event handler functions that act on subtypes of EventBase instances in a Generic way.

# A type variable for a subtype of EventBase
TEvent_contra = TypeVar("TEvent_contra", bound=EventBase, contravariant=True)


class EventHandlerBasicFunc(Protocol[TEvent_contra]):
    """Protocol for a basic event handler function that takes just an event (of subtype of EventBase)."""
    def __call__(self, event_data: TEvent_contra) -> None: ...


class EventHandlerBindableFunc(Protocol[TEvent_contra]):
    """Protocol for an event handler function that takes an event (of subtype of EventBase) and a command sender."""
    def __call__(self, event_data: TEvent_contra, command_sender: StreamDeckCommandSender) -> None: ...


# Type alias for an event handler function that takes an event (of subtype of EventBase), and optionally a command sender.
EventHandlerFunc = Union[EventHandlerBasicFunc[TEvent_contra], EventHandlerBindableFunc[TEvent_contra]]  # noqa: UP007


## Protocols for event handler functions that act on EventBase instances.

class BaseEventHandlerBasicFunc(EventHandlerBasicFunc[EventBase]):
    """Protocol for a basic event handler function that takes just an EventBase."""

class BaseEventHandlerBindableFunc(EventHandlerBindableFunc[EventBase]):
    """Protocol for an event handler function that takes an event (of subtype of EventBase) and a command sender."""


# Type alias for a base event handler function that expects an actual EventBase instance (and optionally a command sender) — used for type hinting internal storage of event handlers.
BaseEventHandlerFunc = Union[BaseEventHandlerBasicFunc, BaseEventHandlerBindableFunc]  # noqa: UP007



# def is_bindable_handler(handler: EventHandlerFunc[TEvent_contra] | BaseEventHandlerFunc) -> TypeIs[EventHandlerBindableFunc[TEvent_contra] | BaseEventHandlerBindableFunc]:
def is_bindable_handler(handler: EventHandlerBasicFunc[TEvent_contra] | EventHandlerBindableFunc[TEvent_contra]) -> TypeIs[EventHandlerBindableFunc[TEvent_contra]]:
    """Check if the handler is prebound with the `command_sender` parameter."""
    # Check dynamically if the `command_sender`'s name is in the handler's arguments.
    return "command_sender" in inspect.signature(handler).parameters
