from __future__ import annotations

from abc import ABC
from collections import defaultdict
from functools import cached_property
from logging import getLogger
from typing import TYPE_CHECKING, cast

from streamdeck.types import BaseEventHandlerFunc


if TYPE_CHECKING:
    from collections.abc import Callable, Generator

    from streamdeck.models.events import EventBase
    from streamdeck.types import EventHandlerFunc, EventNameStr, TEvent_contra


logger = getLogger("streamdeck.actions")


class ActionBase(ABC):
    """Base class for all actions."""

    def __init__(self) -> None:
        """Initialize an Action instance.

        Args:
            uuid (str): The unique identifier for the action.
        """
        self._events: dict[EventNameStr, set[BaseEventHandlerFunc]] = defaultdict(set)

    def on(self, event_name: EventNameStr, /) -> Callable[[EventHandlerFunc[TEvent_contra] | BaseEventHandlerFunc], EventHandlerFunc[TEvent_contra] | BaseEventHandlerFunc]:
        """Register an event handler for a specific event.

        Args:
            event_name (EventNameStr): The name of the event to register the handler for.

        Returns:
            Callable[[EventHandlerFunc], EventHandlerFunc]: A decorator function for registering the event handler.

        Raises:
            KeyError: If the provided event name is not available.
        """
        # if event_name not in DEFAULT_EVENT_NAMES:
        #     msg = f"Provided event name for action handler does not exist: {event_name}"
        #     raise KeyError(msg)

        def _wrapper(func: EventHandlerFunc[TEvent_contra]) -> EventHandlerFunc[TEvent_contra]:
            # Cast to BaseEventHandlerFunc so that the storage type is consistent.
            self._events[event_name].add(cast("BaseEventHandlerFunc", func))

            return func

        return _wrapper

    def get_event_handlers(self, event_name: EventNameStr, /) -> Generator[EventHandlerFunc[EventBase], None, None]:
        """Get all event handlers for a specific event.

        Args:
            event_name (EventName): The name of the event to retrieve handlers for.

        Yields:
            EventHandlerFunc: The event handler functions for the specified event.

        Raises:
            KeyError: If the provided event name is not available.
        """
        # if event_name not in DEFAULT_EVENT_NAMES:
        #     msg = f"Provided event name for pulling handlers from action does not exist: {event_name}"
        #     raise KeyError(msg)

        if event_name not in self._events:
            return

        yield from self._events[event_name]

    def get_registered_event_names(self) -> list[str]:
        """Get all event names for which event handlers are registered.

        Returns:
            list[str]: The list of event names for which event handlers are registered.
        """
        return list(self._events.keys())

class GlobalAction(ActionBase):
    """Represents an action that is performed at the plugin level, meaning it isn't associated with a specific device or action."""


class Action(ActionBase):
    """Represents an action that can be performed for a specific action, with event handlers for specific event types."""

    def __init__(self, uuid: str) -> None:
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


class ActionRegistry:
    """Manages the registration and retrieval of actions and their event handlers."""

    def __init__(self) -> None:
        """Initialize an ActionRegistry instance."""
        self._plugin_actions: list[ActionBase] = []

    def register(self, action: ActionBase) -> None:
        """Register an action with the registry.

        Args:
            action (Action): The action to register.
        """
        self._plugin_actions.append(action)

    def get_action_handlers(self, event_name: EventNameStr, event_action_uuid: str | None = None) -> Generator[EventHandlerFunc[EventBase], None, None]:
        """Get all event handlers for a specific event from all registered actions.

        Args:
            event_name (EventName): The name of the event to retrieve handlers for.
            event_action_uuid (str | None): The action UUID to get handlers for.
                If None (i.e., the event is not action-specific), get all handlers for the event.

        Yields:
            EventHandlerFunc: The event handler functions for the specified event.
        """
        for action in self._plugin_actions:
            # If the event is action-specific (i.e is not a GlobalAction and has a UUID attribute),
            # only get handlers for that action, as we don't want to trigger
            # and pass this event to handlers for other actions.
            if event_action_uuid is not None and (isinstance(action, Action) and action.uuid != event_action_uuid):
                continue

            yield from action.get_event_handlers(event_name)
