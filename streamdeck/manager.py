from __future__ import annotations

import logging
from logging import getLogger
from typing import TYPE_CHECKING

from streamdeck.actions import ActionRegistry
from streamdeck.command_sender import StreamDeckCommandSender
from streamdeck.models.events import event_adapter
from streamdeck.websocket import WebSocketClient


if TYPE_CHECKING:
    from typing import Any, Literal

    from streamdeck.actions import Action
    from streamdeck.models.events import EventBase


# TODO: Fix this up to push to a log in the apropos directory and filename.
logger = getLogger("streamdeck.manager")
logger.addHandler(logging.StreamHandler())



class PluginManager:
    """Manages plugin actions and communicates with a WebSocket server to handle events."""

    def __init__(
        self,
        port: int,
        plugin_uuid: str,  # Passed in by Streamdeck to the entry-point script. should we compare what's in the manifest.json file?
        register_event: Literal["registerPlugin"],  # Passed in by Streamdeck to the entry-point script. Will this always be "registerPlugin"?
        info: dict[str, Any]
    ):
        """Initialize a PluginManager instance.

        Args:
            port (int): The port number for WebSocket connection.
            plugin_uuid (str): The unique identifier for the plugin.
            register_event (str): The registration event type.
            info (dict[str, Any]): The information related to the plugin.
        """
        self._port = port
        self.uuid = plugin_uuid
        self._register_event = register_event
        self._info = info

        self._registry = ActionRegistry()

    def register_action(self, action: Action) -> None:
        """Register an action with the PluginManager.

        Args:
            action (Action): The action to register.
        """
        self._registry.register(action)

    def run(self) -> None:
        """Run the PluginManager by connecting to the WebSocket server and processing incoming events.

        This method establishes a WebSocket connection, registers the plugin, listens for incoming messages,
        and triggers the appropriate action handlers based on the received events.
        """
        with WebSocketClient(port=self._port) as client:
            command_sender = StreamDeckCommandSender(client)

            command_sender.send_action_registration(register_event=self._register_event, plugin_uuid=self.uuid)

            for message in client.listen_forever():
                data: EventBase = event_adapter.validate_json(message)
                logger.debug("Event received: %s", data.event)

                for handler in self._registry.get_action_handlers(data.event): # type: ignore
                    # TODO: from contextual event occurences, save metadata to the action's properties.
                    handler(data)
