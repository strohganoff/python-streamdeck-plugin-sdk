from __future__ import annotations

from typing import TYPE_CHECKING

from streamdeck.event_handlers.actions import Action


if TYPE_CHECKING:
    from collections.abc import Generator

    from streamdeck.event_handlers.protocol import EventHandlerFunc, SupportsEventHandlers
    from streamdeck.types import ActionUUIDStr, EventNameStr


class HandlersRegistry:
    """Manages the registration and retrieval of event handler catalogs and their event handlers."""
    _plugin_event_handler_catalogs: list[SupportsEventHandlers]
    """List of registered actions and other event handler catalogs."""

    def __init__(self) -> None:
        """Initialize a HandlersRegistry instance."""
        self._plugin_event_handler_catalogs = []

    def register(self, catalog: SupportsEventHandlers) -> None:
        """Register an event handler catalog with the registry.

        Args:
            catalog (SupportsEventHandlers): The event handler catalog to register.
        """
        self._plugin_event_handler_catalogs.append(catalog)

    def get_event_handlers(self, event_name: EventNameStr, event_action_uuid: ActionUUIDStr | None = None) -> Generator[EventHandlerFunc, None, None]:
        """Get all event handlers for a specific event from all registered event handler catalogs.

        Args:
            event_name (EventName): The name of the event to retrieve handlers for.
            event_action_uuid (str | None): The action UUID to get handlers for.
                If None (i.e., the event is not action-specific), get all handlers for the event.

        Yields:
            EventHandlerFunc: The event handler functions for the specified event.
        """
        for catalog in self._plugin_event_handler_catalogs:
            # If the event is action-specific (i.e is not a GlobalAction and has a UUID attribute),
            # only get handlers for that action, as we don't want to trigger
            # and pass this event to handlers for other actions.
            if event_action_uuid is not None and (isinstance(catalog, Action) and catalog.uuid != event_action_uuid):
                continue

            yield from catalog.get_event_handlers(event_name)
