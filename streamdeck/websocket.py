"""Async WebSocket transport and Stream Deck event listener."""

from __future__ import annotations

import json
import sys
from logging import getLogger
from typing import TYPE_CHECKING

from websockets.asyncio.client import connect
from websockets.exceptions import (
    ConnectionClosed,
    ConnectionClosedError,
    ConnectionClosedOK,
    WebSocketException,
)

if sys.version_info < (3, 11):
    from exceptiongroup import ExceptionGroup

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


class WebSocketTransport:
    """Own the connection and provide raw asynchronous send and receive calls."""

    def __init__(self, port: int) -> None:
        """Initialize a transport for the local Stream Deck WebSocket server."""
        self._port = port
        self._connection: ClientConnection | None = None

    async def send_event(self, data: dict[str, JsonValue]) -> None:
        """Serialize and send a command through the active connection."""
        if self._connection is None:
            raise ValueError("WebSocket connection not established yet.")

        await self._connection.send(json.dumps(data))

    async def receive(self) -> str | bytes:
        """Receive one frame from the connection.

        The WebSocket event listener is the sole caller of this method.
        """
        if self._connection is None:
            raise ValueError("WebSocket connection not established yet.")

        return await self._connection.recv()

    async def start(self) -> None:
        """Establish the Stream Deck connection."""
        try:
            self._connection = await connect(uri=f"ws://localhost:{self._port}")
        except ConnectionRefusedError:
            logger.exception("Failed to connect to the WebSocket server. Make sure Stream Deck is running.")
            raise

    async def stop(self) -> None:
        """Close the connection if it was established."""
        if self._connection is not None:
            connection = self._connection
            self._connection = None
            await connection.close()

    async def __aenter__(self) -> Self:
        """Open the connection and return the transport."""
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
        except BaseException as cleanup_error:
            if exc_val is None:
                raise
            if isinstance(exc_val, Exception) and isinstance(cleanup_error, Exception):
                raise ExceptionGroup(
                    "WebSocket runtime and connection cleanup both failed",
                    [exc_val, cleanup_error],
                ) from None
            logger.exception(
                "Failed to close WebSocket while handling %s; preserving the active exception",
                exc_type.__name__ if exc_type is not None else "an exception",
            )
        return False


class WebSocketEventListener(EventListener):
    """Yield Stream Deck messages received by a WebSocket transport."""

    event_models: ClassVar[list[type[EventBase]]] = DEFAULT_EVENT_MODELS

    def __init__(self, transport: WebSocketTransport) -> None:
        self._transport = transport

    async def listen(self) -> AsyncIterator[str | bytes]:
        """Yield frames from the transport's single receive loop."""
        try:
            while True:
                yield await self._transport.receive()
        except WebSocketException as exc:
            if isinstance(exc, ConnectionClosedOK):
                logger.debug("Connection was closed normally, stopping the listener.")
            elif isinstance(exc, ConnectionClosedError):
                logger.exception("Connection was terminated with an error.")
            elif isinstance(exc, ConnectionClosed):
                logger.exception("Connection was already closed.")
            else:
                logger.exception("Connection closed due to an unexpected WebSocket error.")

            raise StopStreaming from None
        except Exception:
            logger.exception("Unexpected error while receiving from Stream Deck; stopping the runtime.")
            raise StopStreaming from None

    async def stop(self) -> None:
        """The runtime owns the transport; listener tasks are stopped by cancellation."""
