from __future__ import annotations

import functools
from logging import getLogger
from typing import TYPE_CHECKING

from pydantic import ValidationError

from streamdeck.command_sender import StreamDeckCommandSender
from streamdeck.event_handlers.actions import Action, ActionBase
from streamdeck.event_handlers.protocol import (
    SupportsEventHandlers,
    is_bindable_handler,
    is_not_bindable_handler,
)
from streamdeck.event_handlers.registry import HandlersRegistry
from streamdeck.event_listener import EventListener, EventListenerManager
from streamdeck.models.events.adapter import EventAdapter
from streamdeck.models.events.common import ContextualEventMixin
from streamdeck.utils.logging import configure_streamdeck_logger
from streamdeck.websocket import WebSocketClient


if TYPE_CHECKING:
    from collections.abc import Generator
    from typing import Any, Literal

    from streamdeck.event_handlers.protocol import (
        BindableEventHandlerFunc,
        BoundEventHandlerFunc,
        EventHandlerFunc,
        EventModel_contra,
        InjectableParams,
    )
    from streamdeck.models.events import EventBase



# TODO: Fix this up to push to a log in the apropos directory and filename.
logger = getLogger("streamdeck.manager")


class PluginManager:
    """Manages plugin actions and communicates with a WebSocket server to handle events."""

    def __init__(
        self,
        port: int,
        plugin_uuid: str,
        plugin_registration_uuid: str,  # Passed in by Streamdeck to the entry-point script. should we compare what's in the manifest.json file?
        register_event: Literal["registerPlugin"],  # Passed in by Streamdeck to the entry-point script. Will this always be "registerPlugin"?
        info: dict[str, Any]
    ):
        """Initialize a PluginManager instance.

        Args:
            port (int): The port number for WebSocket connection.
            plugin_uuid (str): The unique identifier for the plugin, as configured in the manifest.json file.
                This can be retrieved either from the manifest.json, or from the -info json object string option passed in by
                the Stream Deck software under `{"plugin": {"uuid": "MY-PLUGIN-UUID"}}`
            plugin_registration_uuid (str): Randomly-generated unique ID passed in by Stream Deck as -pluginUUID option,
                used to send back in the registerPlugin event.
            register_event (str): The registration event type, passed in by the Stream Deck software as -registerEvent option.
                It's value will almost definitely will be "registerPlugin".
            info (dict[str, Any]): The information related to the plugin.
        """
        self._port = port
        self.uuid = plugin_uuid
        self._registration_uuid = plugin_registration_uuid
        self._register_event = register_event
        self._info = info

        self._handlers_registry = HandlersRegistry()
        self._event_listener_manager = EventListenerManager()
        self._event_adapter = EventAdapter()

    def _ensure_catalog_has_valid_events(self, action: SupportsEventHandlers) -> None:
        """Ensure that the event handler catalog's registered events are valid.

        Args:
            action (Action): The action to validate.
        """
        for event_name in action.get_registered_event_names():
            if not self._event_adapter.event_name_exists(event_name):
                msg = f"Invalid event received: {event_name}"
                logger.error(msg)
                raise KeyError(msg)

    def register_action(self, action: ActionBase) -> None:
        """Register an action with the PluginManager, and configure its logger.

        Args:
            action (Action): The action to register.
        """
        # First, validate that the action's registered events are valid.
        self._ensure_catalog_has_valid_events(action)

        # Next, configure a logger for the action, giving it the last part of its uuid as name (if it has one).
        action_component_name = action.uuid.split(".")[-1] if isinstance(action, Action) else "global"
        configure_streamdeck_logger(name=action_component_name, plugin_uuid=self.uuid)

        self._handlers_registry.register(action)

    def register_event_listener(self, listener: EventListener) -> None:
        """Register an event listener with the PluginManager, and add its event models to the event adapter.

        Args:
            listener (EventListener): The event listener to register.
        """
        self._event_listener_manager.add_listener(listener)

        for event_model in listener.event_models:
            self._event_adapter.add_model(event_model)

    def _stream_event_data(self) -> Generator[EventBase, None, None]:
        """Stream event data from the event listeners.

        Validate and model the incoming event data before yielding it.

        Yields:
            EventBase: The event data received from the event listeners.
        """
        for message in self._event_listener_manager.event_stream():
            try:
                data: EventBase = self._event_adapter.validate_json(message)
            except ValidationError:
                logger.exception("Error modeling event data.")
                continue

            logger.debug("Event received: %s", data.event)

            # TODO: is this necessary? Or would this be covered by the event adapter validation?
            if not self._event_adapter.event_name_exists(data.event):
                logger.error("Invalid event received: %s", data.event)
                continue

            yield data

    # def _inject_command_sender(self, handler: EventHandlerFunc[EventModel_contra, InjectableParams], device: DeviceUUIDStr | None, action: ActionUUIDStr | None, action_instance: ActionInstanceUUIDStr | None) -> BoundEventHandlerFunc[EventModel_contra]:
    def _inject_command_sender(self, handler: EventHandlerFunc[EventModel_contra, InjectableParams], command_sender: StreamDeckCommandSender) -> BoundEventHandlerFunc[EventModel_contra]:
        """Inject command_sender into handler if it accepts it as a parameter.

        Args:
            handler: The event handler function
            command_sender: The StreamDeckCommandSender instance

        Returns:
            The handler with command_sender injected if needed
        """
        if is_bindable_handler(handler):
            # If the handler accepts command_sender, inject it and return the handler.
            return functools.partial(handler, command_sender=command_sender)

        if not is_not_bindable_handler(handler):
            # If the handler is neither bindable nor not bindable, raise an error.
            raise TypeError(f"Invalid event handler function signature: {handler}")

        return handler

        # return self._injector.bind_injectable(handler, device, action, action_instance)

    # TODO: rather than an explicit 'command_sender' arg, this will eventually be handled by dynamically binded args.
    def _dispatch_event(self, event: EventBase, command_sender: StreamDeckCommandSender) -> None:
        """Dispatch an event to the appropriate action handlers.

        Args:
            event (EventBase): The event data model for the event to dispatch.
        """
        # If the event is action-specific, we'll pass the action's uuid to the handler to ensure only the correct action is triggered.
        event_action_uuid = event.action if isinstance(event, ContextualEventMixin) else None

        for event_handler in self._handlers_registry.get_event_handlers(event_name=event.event, event_action_uuid=event_action_uuid):
            processed_handler = self._inject_command_sender(event_handler, command_sender)
            # TODO: from contextual event occurrences, save metadata to the action's properties.

            processed_handler(event)

    def run(self) -> None:
        """Run the PluginManager by connecting to the WebSocket server and processing incoming events.

        This method establishes a WebSocket connection, registers the plugin, listens for incoming messages,
        and triggers the appropriate action handlers based on the received events.
        """
        with WebSocketClient(port=self._port) as client:
            # Register the WebSocketClient as an event listener, so we can receive Stream Deck events.
            self.register_event_listener(client)

            command_sender = StreamDeckCommandSender(client, plugin_registration_uuid=self._registration_uuid)
            command_sender.send_action_registration(register_event=self._register_event)

            for data in self._stream_event_data():
                self._dispatch_event(data, command_sender)

            logger.info("PluginManager has stopped processing events.")
