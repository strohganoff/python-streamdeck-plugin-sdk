from __future__ import annotations

import inspect
from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, Protocol

from typing_extensions import Concatenate, ParamSpec, TypeVar  # noqa: UP035

from streamdeck.models.events import EventBase

if TYPE_CHECKING:
    from streamdeck.types import EventNameStr


EventModel_contra = TypeVar("EventModel_contra", bound=EventBase, default=EventBase, contravariant=True)
"""Event model accepted by a handler; contravariance allows handlers for a base event type."""

InjectableHandlerParams = ParamSpec("InjectableHandlerParams", default=...)
"""Handler-specific trailing signature; it may include parameters the SDK cannot inject."""

# The ParamSpec preserves a handler's declared trailing signature at
# registration. Its default ellipsis gives catalogs and dispatch a common type
# with an event-first callable and an otherwise unspecified signature.
EventHandlerFunc = Callable[Concatenate[EventModel_contra, InjectableHandlerParams], None]
"""Event-first callable whose remaining signature is preserved by a ParamSpec.

At registration, the ParamSpec retains the handler's trailing parameter types
and kinds. Dispatch uses the ellipsis default for a shared callable type;
runtime binding decides which named parameters the SDK can provide.
"""


class EventHandlerDecorator(Protocol):
    """Generic registration decorator that preserves each handler's signature."""

    def __call__(
        self,
        func: EventHandlerFunc[EventModel_contra, InjectableHandlerParams],
        /,
    ) -> EventHandlerFunc[EventModel_contra, InjectableHandlerParams]: ...


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


def is_bindable_handler(handler: EventHandlerFunc[EventModel_contra, ...]) -> bool:
    """Check if the handler is prebound with the `command_sender` parameter."""
    # Check dynamically if the `command_sender`'s name is in the handler's arguments.
    return "command_sender" in inspect.signature(handler).parameters


def is_not_bindable_handler(handler: EventHandlerFunc[EventModel_contra, ...]) -> bool:
    """Check if the handler only accepts the event_data parameter.

    If this function returns False after the is_bindable_handler check is True, then the function has invalid parameters, and will subsequently need to be handled in the calling code.
    """
    handler_params = inspect.signature(handler).parameters
    return len(handler_params) == 1 and "event_data" in handler_params








