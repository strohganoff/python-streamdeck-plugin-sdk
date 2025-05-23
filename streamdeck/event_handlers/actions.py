from __future__ import annotations

from abc import ABC
from collections import defaultdict
from functools import cached_property
from logging import getLogger
from typing import TYPE_CHECKING, cast

from streamdeck.event_handlers.protocol import (
    EventHandlerFunc,
    EventModel_contra,
    InjectableParams,
    SupportsEventHandlers,
)


if TYPE_CHECKING:
    from collections.abc import Callable, Generator

    from streamdeck.types import ActionUUIDStr, EventNameStr



logger = getLogger("streamdeck.actions")


class ActionBase(ABC, SupportsEventHandlers):
    """Base class for all actions."""
    _events: dict[EventNameStr, set[EventHandlerFunc]]
    """Dictionary mapping event names to sets of event handler functions."""

    def __init__(self) -> None:
        """Initialize an Action instance."""
        self._events = defaultdict(set)

    def on(self, event_name: EventNameStr, /) -> Callable[[EventHandlerFunc[EventModel_contra, InjectableParams]], EventHandlerFunc[EventModel_contra, InjectableParams]]:
        """Register an event handler for a specific event.

        Args:
            event_name (EventNameStr): The name of the event to register the handler for.

        Returns:
            Callable[[EventHandlerFunc], EventHandlerFunc]: A decorator function for registering the event handler.

        Raises:
            KeyError: If the provided event name is not available.
        """
        def _wrapper(func: EventHandlerFunc[EventModel_contra, InjectableParams]) -> EventHandlerFunc[EventModel_contra, InjectableParams]:
            # Cast to EventHandlerFunc with default type arguments so that the storage type is consistent.
            self._events[event_name].add(cast("EventHandlerFunc", func))
            return func

        return _wrapper

    def get_event_handlers(self, event_name: EventNameStr, /) -> Generator[EventHandlerFunc, None, None]:
        """Get all event handlers for a specific event.

        Args:
            event_name (EventName): The name of the event to retrieve handlers for.

        Yields:
            EventHandlerFunc: The event handler functions for the specified event.

        Raises:
            KeyError: If the provided event name is not available.
        """
        if event_name not in self._events:
            return

        yield from self._events[event_name]

    def get_registered_event_names(self) -> list[EventNameStr]:
        """Get all event names for which event handlers are registered.

        Returns:
            list[str]: The list of event names for which event handlers are registered.
        """
        return list(self._events.keys())


class GlobalAction(ActionBase):
    """Represents an action that is performed at the plugin level, meaning it isn't associated with a specific device or action."""


class Action(ActionBase):
    """Represents an action that can be performed for a specific action, with event handlers for specific event types."""
    uuid: ActionUUIDStr
    """The unique identifier for the action."""

    def __init__(self, uuid: ActionUUIDStr) -> None:
        """Initialize an Action instance.

        Args:
            uuid (str): The unique identifier for the action.
        """
        super().__init__()
        self.uuid = uuid

    @cached_property
    def name(self) -> str:
        """The name of the action, derived from the last part of the UUID."""
        return self.uuid.split(".")[-1]


