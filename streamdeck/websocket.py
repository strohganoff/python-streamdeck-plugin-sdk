"""A client for connecting to the Stream Deck device's WebSocket server and sending/receiving events.

Inherits from the EventListener class to work with the EventListenerManager for processing events.
"""
from __future__ import annotations

import json
from logging import getLogger
from typing import TYPE_CHECKING

from websockets import ConnectionClosedError, WebSocketException
from websockets.exceptions import ConnectionClosed, ConnectionClosedOK
from websockets.sync.client import ClientConnection, connect

from streamdeck.event_listener import EventListener, StopStreaming
from streamdeck.models import events


if TYPE_CHECKING:
    from collections.abc import Generator
    from types import TracebackType
    from typing import Any, ClassVar

    from typing_extensions import Self  # noqa: UP035


logger = getLogger("streamdeck.websocket")



class WebSocketClient(EventListener):
    """A client for connecting to the Stream Deck device's WebSocket server and sending/receiving events."""
    _client: ClientConnection | None

    event_models: ClassVar[list[type[events.EventBase]]] = events.DEFAULT_EVENT_MODELS

    def __init__(self, port: int):
        """Initialize a WebSocketClient instance.

        Args:
            port (int): The port number to connect to the WebSocket server.
        """
        self._port = port
        self._client = None

    def send_event(self, data: dict[str, Any]) -> None:
        """Send an event message to the WebSocket server.

        Args:
            data (dict[str, Any]): The event data to send.
        """
        if self._client is None:
            msg = "WebSocket connection not established yet."
            raise ValueError(msg)

        data_str = json.dumps(data)
        self._client.send(message=data_str)

    def listen(self) -> Generator[str | bytes, Any, None]:
        """Listen for messages from the WebSocket server indefinitely.

        TODO: implement more concise error-handling.

        Yields:
            Union[str, bytes]: The received message from the WebSocket server.
        """
        if self._client is None:
            msg = "WebSocket connection not established yet."
            raise ValueError(msg)

        try:
            while True:
                message: str | bytes = self._client.recv()
                yield message

        except WebSocketException as exc:
            if isinstance(exc, ConnectionClosedOK):
                logger.debug("Connection was closed normally, stopping the client.")
            elif isinstance(exc, ConnectionClosedError):
                logger.exception("Connection was terminated with an error.")
            elif isinstance(exc, ConnectionClosed):
                logger.exception("Connection was already closed.")
            else:
                logger.exception("Connection is closed due to an unexpected WebSocket error.")

            raise StopStreaming from None

        except Exception:
            logger.exception("Failed to receive messages from websocket server due to unexpected error.")
            raise

    def start(self) -> None:
        """Start the connection to the websocket server."""
        try:
            self._client = connect(uri=f"ws://localhost:{self._port}")
        except ConnectionRefusedError:
            logger.exception("Failed to connect to the WebSocket server. Make sure the Stream Deck software is running.")
            raise

    def stop(self) -> None:
        """Close the WebSocket connection, if open."""
        if self._client is not None:
            self._client.close()

    def __enter__(self) -> Self:
        """Start the connection to the websocket server.

        Returns:
            Self: The WebSocketClient instance after connecting to the WebSocket server.
        """
        self.start()
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> None:
        """Close the WebSocket connection, if open."""
        self.stop()

