"""Registry for action and plugin event handler catalogs."""

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

    def iter_event_handler_bindings(
        self,
        event_name: EventNameStr | ALL_EVENTS = ALL_EVENTS,
        event_action_uuid: ActionUUIDStr | None = None,
    ) -> Iterator[tuple[EventNameStr, EventHandlerFunc]]:
        """Yield registered event names with their handlers, optionally filtered.

        Args:
            event_name: The event name to retrieve, or ``ALL_EVENTS`` to enumerate every
                registered event.
            event_action_uuid: The action UUID to filter action-specific catalogs by. If None,
                include handlers from all catalogs.

        Yields:
            A registered event name and its handler.
        """
        for catalog in self._plugin_event_handler_catalogs:
            if event_action_uuid is not None and (isinstance(catalog, Action) and catalog.uuid != event_action_uuid):
                continue

            for catalog_event_name in (
                (event_name,)
                if event_name is not ALL_EVENTS
                else catalog.get_registered_event_names()
            ):
                for handler in catalog.get_event_handlers(catalog_event_name):
                    yield catalog_event_name, handler

    def get_event_handlers(
        self,
        event_name: EventNameStr | ALL_EVENTS,
        event_action_uuid: ActionUUIDStr | None = None,
    ) -> Iterator[EventHandlerFunc]:
        """Yield handlers matching an event name or enumerate all registrations.

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
        for _, handler in self.iter_event_handler_bindings(event_name, event_action_uuid):
            yield handler
