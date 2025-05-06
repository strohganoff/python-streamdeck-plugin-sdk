from __future__ import annotations

from typing import TYPE_CHECKING

from streamdeck.event_handlers.actions import Action


if TYPE_CHECKING:
    from collections.abc import Generator

    from streamdeck.event_handlers.protocol import EventHandlerFunc, SupportsEventHandlers
    from streamdeck.types import ActionUUIDStr, EventNameStr


class HandlersRegistry:
    """Manages the registration and retrieval of actions and their event handlers."""
    _plugin_actions: list[SupportsEventHandlers]
    """List of registered actions."""

    def __init__(self) -> None:
        """Initialize an HandlersRegistry instance."""
        self._plugin_actions = []

    def register(self, action: SupportsEventHandlers) -> None:
        """Register an action with the registry.

        Args:
            action (Action): The action to register.
        """
        self._plugin_actions.append(action)

    def get_event_handlers(self, event_name: EventNameStr, event_action_uuid: ActionUUIDStr | None = None) -> Generator[EventHandlerFunc, None, None]:
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
