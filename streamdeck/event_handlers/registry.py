from __future__ import annotations

from typing import TYPE_CHECKING
from typing_extensions import sentinel

from streamdeck.event_handlers.actions import Action


if TYPE_CHECKING:
    from collections.abc import Iterator

    from streamdeck.event_handlers.protocol import EventHandlerFunc, SupportsEventHandlers
    from streamdeck.types import ActionUUIDStr, EventNameStr


ALL_EVENTS = sentinel("ALL_EVENTS")
"""Sentinel for enumerating all currently registered event handlers."""


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

    def get_event_handlers(
        self,
        event_name: EventNameStr | ALL_EVENTS,
        event_action_uuid: ActionUUIDStr | None = None,
    ) -> Iterator[EventHandlerFunc]:
        """Get handlers matching an event name or enumerate all registrations.

        Passing ``ALL_EVENTS`` enumerates handlers registered under every event
        name. It does not register a handler to receive every event.

        Args:
            event_name (EventNameStr | ALL_EVENTS): The event name to retrieve,
                or ``ALL_EVENTS`` to enumerate every registered event.
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

            for catalog_event_name in (
                (event_name,)
                if event_name is not ALL_EVENTS
                else catalog.get_registered_event_names()
            ):
                yield from catalog.get_event_handlers(catalog_event_name)
