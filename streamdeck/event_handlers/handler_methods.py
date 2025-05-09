from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Generic, Protocol, cast, runtime_checkable

from typing_extensions import Self, TypeVar  # noqa: UP035

from streamdeck.event_handlers.protocol import (
    EventModel_contra,
    SupportsEventHandlers,
)


if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from types import FunctionType

    from streamdeck.event_handlers.protocol import BoundEventHandlerFunc
    from streamdeck.types import EventNameStr




M_contra = TypeVar("M_contra", bound="HandlerMethodCatalogMixin", contravariant=True)


@runtime_checkable
class EventHandlerMethod(Protocol[M_contra, EventModel_contra]):
    """Protocol for a method of a HandlerMethodCatalogMixin subclass that is an event handler.

    Methods annotated with this protocol are expected to be instance methods decorated with the @on decorator.
    """

    # The `self` arg in a protocol's method is treated differently than in a normal method.
    # It is not bound to the instance of the class, but rather to the type/object of the thing being annotated with this protocol.
    # This means that `self` doesn't represent the encompassing class of the method, but rather the class/type of the method itself.
    # The recommended way to handle this is to include the `__self` argument in the method signature to represent the instance of the class that the method is bound to.
    def __call__(self, __self: M_contra, event_data: EventModel_contra) -> None:  # noqa: PYI063
        """Handle the event with the given event data.

        Args:
            event_data (EventBase): The data associated with the event.
        """


@runtime_checkable
class MarkedEventHandlerMethod(EventHandlerMethod[M_contra, EventModel_contra], Protocol):
    """Protocol for a marked method of a HandlerMethodCatalogMixin subclass that is an event handler.

    Methods annotated with this protocol are expected to have been decorated and passed through the @on decorator,
    which will have given them the __handles_event__ attribute.

    """
    __handles_event__: EventNameStr
    """The name of the event that this handler is associated with."""


def on(event_name: EventNameStr) -> Callable[[EventHandlerMethod[M_contra, EventModel_contra]], MarkedEventHandlerMethod[M_contra, EventModel_contra]]:
    """Decorator to have an HandlerMethodCatalogMixin subclass register a method as an event handler for a specific event.

    Args:
        event_name (EventNameStr): The name of the event to register the handler for.

    Returns:
        Callable[[EventHandlerMethod], MarkedEventHandlerMethod]: An inner wrapper function that marks the event handler.
    """
    def decorator(func: EventHandlerMethod[M_contra, EventModel_contra]) -> MarkedEventHandlerMethod[M_contra, EventModel_contra]:
        """Inner wrapper function that marks the event handler with the event name.

        The HandlerMethodCatalogMixin.__init_subclass__ method will do the rest of the work to collect the event handlers marked by this decorator.
        """
        func.__handles_event__ = event_name  # type: ignore[attr-defined]
        return cast("MarkedEventHandlerMethod[M_contra, EventModel_contra]", func)
    return decorator


class HandlerMethodCatalogMixin(SupportsEventHandlers, Generic[EventModel_contra]):
    """Mixin class for classes that define their event handlers on their own method definitions, and collect them at the class-level.

    This contrasts with the ActionBase class, which has an instance method to decorate any function as an event handler (e.g. at the instance-level).
    """
    _handlers: dict[EventNameStr, list[MarkedEventHandlerMethod[Self, EventModel_contra]]]
    """A dictionary of event names to lists of event handler methods.

    Each subclass of this mixin will have its own dictionary of event handlers (instantiated in the __init_subclass__ method),
    so that they don't interfere with each other.
    For this reason, we don't annotate this as a ClassVar, since it is not shared across all subclasses.
    """

    @classmethod
    def __init_subclass__(cls) -> None:
        # Initialize a unique _events dictionary for each subclass
        cls._handlers = defaultdict(list)

        for method in cls.__dict__.values():
            if isinstance(method, MarkedEventHandlerMethod):
                cls._handlers[method.__handles_event__].append(method)  # type: ignore[attr-defined]

    def get_event_handlers(self, event_name: EventNameStr) -> Generator[BoundEventHandlerFunc, None, None]:
        """Get all event handlers for a specific event.

        Each event handler will be bound to the current instance of the class before being yielded, so the downstream caller
        doesn't need to handle logic for calling an instance method vs a standalone function,
        and the methods themselves can still access the instance via the `self` argument.

        To do this, we manually call the __get__ method of the function to bind it to the current instance.
        This is similar to how the @staticmethod and @classmethod decorators work in Python.

        Args:
            event_name (str): The name of the event to get handlers for.

        Returns:
            list[BoundEventHandlerFunc]: The event handler functions for the specified event.
                Subclasses of this mixin don't yet support any injectable parameters, so the return type doesn't include any.
                Also, HandlerRegistry expects event handlers to not be unbound methods (Thing().method, where method has a self argument),
                but rather bound methods (where Thing.method is like a static method, and doesn't have a self argument),
                so we need to bind each method to the current instance before yielding it.
        """
        for handler in self._handlers.get(event_name, []):
            # Use the default descripter __get__(instance: object, owner: type) method to manually bind the method to the instance
            # so that we can yield the real bound-method object, which will be called with the instance as the first argument.
            yield cast("FunctionType", handler).__get__(self, self.__class__)

    def get_registered_event_names(self) -> list[EventNameStr]:
        """Get all event names for which handlers are registered.

        Returns:
            list[str]: A list of event names for which handlers are registered.
        """
        return list(self._handlers.keys())
