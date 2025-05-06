from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Protocol, cast

from typing_extensions import TypeVar, override  # noqa: UP035

from streamdeck.event_handlers.protocol import (
    EventHandlerFunc,
    EventModel_contra,
    SupportsEventHandlers,
)


if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from types import FunctionType
    from typing import ClassVar

    from streamdeck.types import EventNameStr



# Implicitly matches the `SupportsEventHandlers` protocol. We don't explicitly include it here to avoid a metaclass conflict.
class HandlerMethodCatalogMixin(SupportsEventHandlers):
    """Mixin class for classes that define their event handlers on their own method definitions, and collect them at the class-level.

    This contrasts with the ActionBase class, which has an instance method to decorate any function as an event handler (e.g. at the instance-level).
    """
    _handlers: ClassVar[dict[EventNameStr, list[EventHandlerFunc]]]

    @classmethod
    def __init_subclass__(cls) -> None:
        # Initialize a unique _events dictionary for each subclass
        cls._handlers = defaultdict(list)

        for method in cls.__dict__.values():
            if not callable(method):
                continue

            handled_event_name = getattr(method, "_handles_event", None)
            if handled_event_name:
                cls._handlers[handled_event_name].append(method)  # type: ignore[attr-defined]

    def get_event_handlers(self, event_name: EventNameStr) -> Generator[EventHandlerFunc, None, None]:
        """Get all event handlers for a specific event.

        Args:
            event_name (str): The name of the event to get handlers for.

        Returns:
            list[EventHandlerFunc]: The event handler functions for the specified event.
        """
        for handler in self._handlers.get(event_name, []):
            # Use the default descripter __get__(instance: object, owner: type) method to bind the method to the instance
            # so that we can yield the real bound-method object, which will be called with the instance as the first argument.
            yield cast("FunctionType", handler).__get__(self, self.__class__)

    def get_registered_event_names(self) -> list[EventNameStr]:
        """Get all event names for which handlers are registered.

        Returns:
            list[str]: A list of event names for which handlers are registered.
        """
        return list(self._handlers.keys())


M_contra = TypeVar("M_contra", bound="HandlerMethodCatalogMixin", contravariant=True)


class InjectableEventHandler(Protocol[M_contra, EventModel_contra]):
    """Protocol for an Injectable's event handler function."""

    def __call__(self, __self: M_contra, event_data: EventModel_contra) -> None:
        """Handle the event with the given event data.

        Args:
            event_data (EventBase): The data associated with the event.
        """


class MarkedInjectableEventHandler(InjectableEventHandler[M_contra, EventModel_contra], Protocol):
    """Protocol for an Injectable's event handler function that has been marked by the @on decorator."""
    _handles_event: EventNameStr
    """The name of the event that this handler is associated with."""

    # TODO: Do I need to use ParamSpec here, or implement into already implemented handler types?
    @override
    def __call__(self, event_data: EventModel_contra) -> None: ...  # type: ignore[override]


def on(event_name: EventNameStr) -> Callable[[InjectableEventHandler[M_contra, EventModel_contra]], MarkedInjectableEventHandler[M_contra, EventModel_contra]]:
    """Decorator to have an Injectable subclass register a method as an event handler for a specific event.

    Args:
        event_name (EventNameStr): The name of the event to register the handler for.

    Returns:
        Callable[[InjectableEventHandler], MarkedInjectableEventHandler]: An inner wrapper function that marks the event handler.
    """
    def decorator(func: InjectableEventHandler[M_contra, EventModel_contra]) -> MarkedInjectableEventHandler[M_contra, EventModel_contra]:
        """Inner wrapper function that marks the event handler with the event name.

        The Injectable.__init_subclass__ method will do the rest of the work to collect the event handlers marked by this decorator.
        """
        func._handles_event = event_name  # type: ignore[attr-defined]  # noqa: SLF001
        return cast("MarkedInjectableEventHandler[M_contra, EventModel_contra]", func)
    return decorator
