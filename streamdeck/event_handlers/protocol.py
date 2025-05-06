from __future__ import annotations

import inspect
from collections.abc import Iterable
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from typing_extensions import ParamSpec, TypeGuard, TypeVar  # noqa: UP035

from streamdeck.command_sender import StreamDeckCommandSender
from streamdeck.models.events import EventBase


if TYPE_CHECKING:
    from collections.abc import Iterable

    from streamdeck.types import EventNameStr



EventModel_contra = TypeVar("EventModel_contra", bound=EventBase, default=EventBase, contravariant=True)
InjectableParams = ParamSpec("InjectableParams", default=...)


class EventHandlerFunc(Protocol[EventModel_contra, InjectableParams]):
    """Protocol for an event handler function that takes an event (of subtype of EventBase) and other parameters that are injectable."""
    def __call__(self, event_data: EventModel_contra, *args: InjectableParams.args, **kwargs: InjectableParams.kwargs) -> None: ...


BindableEventHandlerFunc = EventHandlerFunc[EventModel_contra, tuple[StreamDeckCommandSender]]  # type: ignore[misc]
"""Type alias for a bindable event handler function that takes an event (of subtype of EventBase) and a command_sender parameter that is to be injected."""
BoundEventHandlerFunc = EventHandlerFunc[EventModel_contra]
"""Type alias for a bound event handler function that takes an event (of subtype of EventBase) and no other parameters.

Typically used for event handlers that have already had parameters injected.
"""


@runtime_checkable
class SupportsEventHandlers(Protocol):
    """Protocol for a class that holds event-specific handler functions which can be pulled out by event name.

    Implementing classes should handle defining the registration of event handlers and ensuring
    that they can be retrieved efficiently.
    """

    def get_event_handlers(self, event_name: EventNameStr, /) -> Iterable[EventHandlerFunc]:
        """Get all event handlers for a specific event.

        Args:
            event_name (str): The name of the event to get handlers for.

        Returns:
            Iterable[EventHandlerFunc]: The event handler functions for the specified event.
        """
        ...

    def get_registered_event_names(self) -> list[EventNameStr]:
        """Get all event names for which handlers are registered.

        Returns:
            list[str]: A list of event names for which handlers are registered.
        """
        ...


# def is_bindable_handler(handler: EventHandlerFunc[EventModel_contra, InjectableParams]) -> TypeGuard[BindableEventHandlerFunc[EventModel_contra]]:
def is_bindable_handler(handler: EventHandlerFunc[EventModel_contra, InjectableParams]) -> bool:
    """Check if the handler is prebound with the `command_sender` parameter."""
    # Check dynamically if the `command_sender`'s name is in the handler's arguments.
    return "command_sender" in inspect.signature(handler).parameters


def is_not_bindable_handler(handler: EventHandlerFunc[EventModel_contra, InjectableParams]) -> TypeGuard[BoundEventHandlerFunc[EventModel_contra]]:
    """Check if the handler only accepts the event_data parameter.

    If this function returns False after the is_bindable_handler check is True, then the function has invalid parameters, and will subsequently need to be handled in the calling code.
    """
    handler_params = inspect.signature(handler).parameters
    return len(handler_params) == 1 and "event_data" in handler_params








