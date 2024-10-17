from __future__ import annotations

from collections import defaultdict
from logging import getLogger
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Callable, Generator

    from streamdeck.types import EventHandlerFunc, EventNameStr


logger = getLogger("streamdeck.actions")



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


class Action:
    """Represents an action that can be performed, with event handlers for specific event types."""

    def __init__(self, uuid: str):
        """Initialize an Action instance.

        Args:
            uuid (str): The unique identifier for the action.
        """
        self.uuid = uuid

        self._events: dict[EventNameStr, set[EventHandlerFunc]] = defaultdict(set)

    def on(self, event_name: EventNameStr, /) -> Callable[[EventHandlerFunc], EventHandlerFunc]:
        """Register an event handler for a specific event.

        Args:
            event_name (EventNameStr): The name of the event to register the handler for.

        Returns:
            Callable[[EventHandlerFunc], EventHandlerFunc]: A decorator function for registering the event handler.

        Raises:
            KeyError: If the provided event name is not available.
        """
        if event_name not in available_event_names:
            msg = f"Provided event name for action handler does not exist: {event_name}"
            raise KeyError(msg)

        def _wrapper(func: EventHandlerFunc) -> EventHandlerFunc:
            self._events[event_name].add(func)

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
        if event_name not in available_event_names:
            msg = f"Provided event name for pulling handlers from action does not exist: {event_name}"
            raise KeyError(msg)

        for event in self._events[event_name]:
            yield event


class ActionRegistry:
    """Manages the registration and retrieval of actions and their event handlers."""

    def __init__(self):
        """Initialize an ActionRegistry instance."""
        self._plugin_actions: list[Action] = []

    def register(self, action: Action) -> None:
        """Register an action with the registry.

        Args:
            action (Action): The action to register.
        """
        self._plugin_actions.append(action)

    def get_action_handlers(self, event_name: EventNameStr) -> Generator[EventHandlerFunc, None, None]:
        """Get all event handlers for a specific event from all registered actions.

        Args:
            event_name (EventName): The name of the event to retrieve handlers for.

        Yields:
            EventHandlerFunc: The event handler functions for the specified event.
        """
        for action in self._plugin_actions:
            yield from action.get_event_handlers(event_name)




