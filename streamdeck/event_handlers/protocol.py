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
    """Check if a handler can be called with only its event parameter.

    Optional parameters and variadic parameters are allowed, as they don't
    prevent dispatch from calling the handler with just the event data.
    """
    if is_bindable_handler(handler):
        return False

    try:
        inspect.signature(handler).bind(object())
    except TypeError:
        return False
    return True


def validate_event_handler_signature(handler: EventHandlerFunc[EventModel_contra, ...]) -> None:
    """Validate that dispatch can call a handler with its event and SDK injections.

    The event must be the required first positional parameter. The current
    registry provides ``command_sender`` by keyword; any other parameters must
    be optional or variadic.

    Raises:
        TypeError: If the handler signature cannot be satisfied by dispatch.
    """
    try:
        handler_signature = inspect.signature(handler)
    except (TypeError, ValueError) as exc:
        msg = f"Cannot inspect event handler signature: {handler!r}"
        raise TypeError(msg) from exc

    event_parameter = next(iter(handler_signature.parameters.values()), None)
    if event_parameter is None:
        msg = f"Invalid event handler signature for {handler!r}: expected a required positional 'event_data' parameter first"
        raise TypeError(msg)

    if (
        event_parameter.name != "event_data"
        or event_parameter.kind not in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        or event_parameter.default is not inspect.Parameter.empty
    ):
        msg = f"Invalid event handler signature for {handler!r}: expected a required positional 'event_data' parameter first"
        raise TypeError(msg)

    command_sender_parameter = handler_signature.parameters.get("command_sender")
    if command_sender_parameter is not None and command_sender_parameter.kind not in (
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
        inspect.Parameter.KEYWORD_ONLY,
    ):
        msg = f"Invalid event handler signature for {handler!r}: 'command_sender' must accept a keyword argument"
        raise TypeError(msg)

    # Check that dispatch can satisfy every required parameter without calling the handler.
    # Simulate dispatch's call shape: event_data positionally, plus command_sender by keyword when declared.
    # Binding fails if any required parameter is missing.
    bind_kwargs = {"command_sender": object()} if command_sender_parameter is not None else {}
    try:
        handler_signature.bind(object(), **bind_kwargs)
    except TypeError as exc:
        msg = f"Invalid event handler signature for {handler!r}: {exc}"
        raise TypeError(msg) from exc
