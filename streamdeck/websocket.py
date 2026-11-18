"""Connect to Stream Deck's WebSocket server and send or receive events.

`WebSocketClient` implements :class:`~streamdeck.event_listener.EventListener`:
its async `listen()` iterator yields inbound messages to the
`EventListenerManager`, which merges them with messages from custom
listeners. The client is the sole reader of the Stream Deck connection.

Outbound commands use the same active connection through `send_event()`.
The `StreamDeckCommandSender` builds command payloads and delegates sending
to this client; connection setup and cleanup remain owned by the runtime via
the client's async context manager.
"""
from __future__ import annotations

import json
from logging import getLogger
from typing import TYPE_CHECKING

from websockets.asyncio.client import connect
from websockets.exceptions import (
    ConnectionClosed,
    ConnectionClosedError,
    ConnectionClosedOK,
    WebSocketException,
)

from streamdeck.event_listener import EventListener, StopStreaming
from streamdeck.models.events import DEFAULT_EVENT_MODELS


if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from types import TracebackType
    from typing import ClassVar

    from pydantic import JsonValue
    from typing_extensions import Self
    from websockets.asyncio.client import ClientConnection

    from streamdeck.models.events import EventBase


logger = getLogger("streamdeck.websocket")


class WebSocketClient(EventListener):
    """The sole reader and async sender for the active Stream Deck connection."""

    event_models: ClassVar[list[type[EventBase]]] = DEFAULT_EVENT_MODELS

    def __init__(self, port: int) -> None:
        """Initialize the client for the Stream Deck WebSocket server.

        The connection is established later by :meth:`start`, so constructing
        a client does not perform network I/O.

        Args:
            port: The local port number provided by Stream Deck for the
                WebSocket connection.
        """
        self._port = port
        self._client: ClientConnection | None = None

    async def send_event(self, data: dict[str, JsonValue]) -> None:
        """Serialize and send a command through the active connection."""
        if self._client is None:
            raise ValueError("WebSocket connection not established yet.")

        await self._client.send(json.dumps(data))

    async def listen(self) -> AsyncIterator[str | bytes]:
        """Yield inbound frames; this is the connection's only receive loop."""
        if self._client is None:
            raise ValueError("WebSocket connection not established yet.")

        try:
            while True:
                yield await self._client.recv()
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
            logger.exception("Unexpected error while receiving from Stream Deck; stopping the runtime.")
            raise StopStreaming from None

    async def start(self) -> None:
        """Establish the Stream Deck connection."""
        try:
            self._client = await connect(uri=f"ws://localhost:{self._port}")
        except ConnectionRefusedError:
            logger.exception("Failed to connect to the WebSocket server. Make sure Stream Deck is running.")
            raise

    async def stop(self) -> None:
        """Close the connection if it was established."""
        if self._client is not None:
            await self._client.close()
            self._client = None

    async def __aenter__(self) -> Self:
        """Open the connection and return this client for an `async with` block.

        Returns:
            Self: The WebSocketClient instance after connecting to the WebSocket server.
        """
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        """Close the connection, preserving any exception from the block."""
        try:
            await self.stop()
        except BaseException:
            if exc_val is None:
                raise
            logger.exception(
                "Failed to close WebSocket while handling %s",
                exc_type.__name__ if exc_type is not None else "an exception",
            )
        return False
