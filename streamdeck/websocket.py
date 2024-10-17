from __future__ import annotations

import json
from logging import getLogger
from typing import TYPE_CHECKING

from websockets.exceptions import ConnectionClosed, ConnectionClosedError, ConnectionClosedOK
from websockets.sync.client import ClientConnection, connect


if TYPE_CHECKING:
    from collections.abc import Generator
    from typing import Any

    from typing_extensions import Self


logger = getLogger("streamdeck.websocket")



class WebSocketClient:
    """A client for connecting to the Stream Deck device's WebSocket server and sending/receiving events."""
    _client: ClientConnection | None

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
        data_str = json.dumps(data)
        self._client.send(message=data_str)

    def listen_forever(self) -> Generator[str | bytes, Any, None]:
        """Listen for messages from the WebSocket server indefinitely.

        TODO: implement more concise error-handling.

        Yields:
            Union[str, bytes]: The received message from the WebSocket server.
        """
        # TODO: Check that self._client is a connected thing.
        try:
            while True:
                message: str | bytes = self._client.recv()
                yield message

        except Exception:
            logger.exception("Failed to receive messages from websocket server.")

    def __enter__(self) -> Self:
        """Start the connection to the websocket server.

        Returns:
            Self: The WebSocketClient instance after connecting to the WebSocket server.
        """
        self._client = connect(uri=f"ws://localhost:{self._port}")
        return self

    def __exit__(self, *args, **kwargs) -> None:
        """Close the WebSocket connection, if open."""
        if self._client is not None:
            self._client.close()

