from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Protocol, TypeVar, Union

from streamdeck.models.events import DEFAULT_EVENT_NAMES, EventBase


if TYPE_CHECKING:
    from typing_extensions import TypeAlias, TypeIs  # noqa: UP035

    from streamdeck.command_sender import StreamDeckCommandSender



EventNameStr: TypeAlias = str  # noqa: UP040
"""Type alias for the event name string.

We don't define literal string values here, as the list of available event names can be added to dynamically.
"""


def is_valid_event_name(event_name: str) -> TypeIs[EventNameStr]:
    """Check if the event name is one of the available event names."""
    return event_name in DEFAULT_EVENT_NAMES


### Event Handler Type Definitions ###

## Protocols for event handler functions that act on subtypes of EventBase instances in a Generic way.

TEvent_contra = TypeVar("TEvent_contra", bound=EventBase, contravariant=True)
"""Type variable for a subtype of EventBase."""


class EventHandlerBasicFunc(Protocol[TEvent_contra]):
    """Protocol for a basic event handler function that takes just an event (of subtype of EventBase)."""
    def __call__(self, event_data: TEvent_contra) -> None: ...


class EventHandlerBindableFunc(Protocol[TEvent_contra]):
    """Protocol for an event handler function that takes an event (of subtype of EventBase) and a command sender."""
    def __call__(self, event_data: TEvent_contra, command_sender: StreamDeckCommandSender) -> None: ...


EventHandlerFunc = Union[EventHandlerBasicFunc[TEvent_contra], EventHandlerBindableFunc[TEvent_contra]]  # noqa: UP007
"""Type alias for an event handler function that takes an event (of subtype of EventBase), and optionally a command sender."""


## Protocols for event handler functions that act on EventBase instances.

class BaseEventHandlerBasicFunc(EventHandlerBasicFunc[EventBase]):
    """Protocol for a basic event handler function that takes just an EventBase."""

class BaseEventHandlerBindableFunc(EventHandlerBindableFunc[EventBase]):
    """Protocol for an event handler function that takes an event (of subtype of EventBase) and a command sender."""


BaseEventHandlerFunc = Union[BaseEventHandlerBasicFunc, BaseEventHandlerBindableFunc]  # noqa: UP007
"""Type alias for a base event handler function that takes an actual EventBase instance argument, and optionally a command sender.

This is used for type hinting internal storage of event handlers.
"""



# def is_bindable_handler(handler: EventHandlerFunc[TEvent_contra] | BaseEventHandlerFunc) -> TypeIs[EventHandlerBindableFunc[TEvent_contra] | BaseEventHandlerBindableFunc]:
def is_bindable_handler(handler: EventHandlerBasicFunc[TEvent_contra] | EventHandlerBindableFunc[TEvent_contra]) -> TypeIs[EventHandlerBindableFunc[TEvent_contra]]:
    """Check if the handler is prebound with the `command_sender` parameter."""
    # Check dynamically if the `command_sender`'s name is in the handler's arguments.
    return "command_sender" in inspect.signature(handler).parameters
