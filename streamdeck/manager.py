from __future__ import annotations

import functools
from logging import getLogger
from typing import TYPE_CHECKING

from streamdeck.actions import Action, ActionBase, ActionRegistry
from streamdeck.command_sender import StreamDeckCommandSender
from streamdeck.models.events import ContextualEventMixin, event_adapter
from streamdeck.types import (
    EventHandlerBasicFunc,
    EventHandlerFunc,
    TEvent_contra,
    is_bindable_handler,
    is_valid_event_name,
)
from streamdeck.utils.logging import configure_streamdeck_logger
from streamdeck.websocket import WebSocketClient


if TYPE_CHECKING:
    from typing import Any, Literal

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

        self._registry = ActionRegistry()

    def register_action(self, action: ActionBase) -> None:
        """Register an action with the PluginManager, and configure its logger.

        Args:
            action (Action): The action to register.
        """
        # First, configure a logger for the action, giving it the last part of its uuid as name (if it has one).
        action_component_name = action.uuid.split(".")[-1] if isinstance(action, Action) else "global"
        configure_streamdeck_logger(name=action_component_name, plugin_uuid=self.uuid)

        self._registry.register(action)

    def _inject_command_sender(self, handler: EventHandlerFunc[TEvent_contra], command_sender: StreamDeckCommandSender) -> EventHandlerBasicFunc[TEvent_contra]:
        """Inject command_sender into handler if it accepts it as a parameter.

        Args:
            handler: The event handler function
            command_sender: The StreamDeckCommandSender instance

        Returns:
            The handler with command_sender injected if needed
        """
        if is_bindable_handler(handler):
            return functools.partial(handler, command_sender=command_sender)

        return handler

    def run(self) -> None:
        """Run the PluginManager by connecting to the WebSocket server and processing incoming events.

        This method establishes a WebSocket connection, registers the plugin, listens for incoming messages,
        and triggers the appropriate action handlers based on the received events.
        """
        with WebSocketClient(port=self._port) as client:
            command_sender = StreamDeckCommandSender(client, plugin_registration_uuid=self._registration_uuid)

            command_sender.send_action_registration(register_event=self._register_event, plugin_registration_uuid=self._registration_uuid)

            for message in client.listen():
                data: EventBase = event_adapter.validate_json(message)

                if not is_valid_event_name(data.event):
                    logger.error("Received event name is not valid: %s", data.event)
                    continue

                logger.debug("Event received: %s", data.event)

                # If the event is action-specific, we'll pass the action's uuid to the handler to ensure only the correct action is triggered.
                event_action_uuid = data.action if isinstance(data, ContextualEventMixin) else None

                for event_handler in self._registry.get_action_handlers(event_name=data.event, event_action_uuid=event_action_uuid):
                    processed_handler = self._inject_command_sender(event_handler, command_sender)
                    # TODO: from contextual event occurences, save metadata to the action's properties.

                    processed_handler(data)


