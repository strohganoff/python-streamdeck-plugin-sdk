from __future__ import annotations

import asyncio
import json
import logging
from unittest.mock import AsyncMock, Mock

import pytest
from websockets.exceptions import (
    ConnectionClosed,
    ConnectionClosedError,
    ConnectionClosedOK,
    WebSocketException,
)

from streamdeck.event_listener import StopStreaming
from streamdeck.websocket import WebSocketClient


def test_start_send_and_stop(monkeypatch: pytest.MonkeyPatch, port_number: int) -> None:
    async def scenario() -> None:
        connection = Mock()
        connection.send = AsyncMock()
        connection.close = AsyncMock()
        connect_mock = AsyncMock(return_value=connection)
        monkeypatch.setattr("streamdeck.websocket.connect", connect_mock)
        client = WebSocketClient(port_number)
        await client.start()
        connect_mock.assert_awaited_once_with(uri=f"ws://localhost:{port_number}")
        payload = {"event": "test", "payload": {"k": "v"}}
        await client.send_event(payload)
        connection.send.assert_awaited_once_with(json.dumps(payload))
        await client.stop()
        connection.close.assert_awaited_once()
        assert client._client is None

    asyncio.run(scenario())


def test_async_context_manager_starts_and_closes_connection(
    monkeypatch: pytest.MonkeyPatch,
    port_number: int,
) -> None:
    async def scenario() -> None:
        connection = Mock()
        connection.close = AsyncMock()
        connect_mock = AsyncMock(return_value=connection)
        monkeypatch.setattr("streamdeck.websocket.connect", connect_mock)
        client = WebSocketClient(port_number)
        async with client as active_client:
            assert active_client is client
            assert client._client is connection
        connect_mock.assert_awaited_once_with(uri=f"ws://localhost:{port_number}")
        connection.close.assert_awaited_once()
        assert client._client is None

    asyncio.run(scenario())


def test_listen_yields_frames_and_stops_on_connection_close(port_number: int) -> None:
    async def scenario() -> None:
        client = WebSocketClient(port_number)
        connection = Mock()
        connection.recv = AsyncMock(side_effect=["text", b"binary", ConnectionClosed(None, None)])
        client._client = connection
        received: list[str | bytes] = []
        with pytest.raises(StopStreaming):
            async for message in client.listen():
                received.append(message)
        assert received == ["text", b"binary"]

    asyncio.run(scenario())


def test_listen_translates_websocket_errors_to_stop_streaming(port_number: int) -> None:
    async def scenario() -> None:
        client = WebSocketClient(port_number)
        connection = Mock()
        connection.recv = AsyncMock(side_effect=WebSocketException("broken"))
        client._client = connection
        with pytest.raises(StopStreaming):
            async for _ in client.listen():
                pass

    asyncio.run(scenario())


def test_listen_translates_unexpected_receive_errors_to_stop_streaming(
    port_number: int,
    caplog: pytest.LogCaptureFixture,
) -> None:
    async def scenario() -> None:
        client = WebSocketClient(port_number)
        connection = Mock()
        connection.recv = AsyncMock(side_effect=RuntimeError("unexpected receive failure"))
        client._client = connection
        with pytest.raises(StopStreaming):
            async for _ in client.listen():
                pass

    asyncio.run(scenario())

    assert "Unexpected error while receiving from Stream Deck; stopping the runtime." in caplog.text


@pytest.mark.parametrize(
    ("error", "level", "message"),
    [
        (ConnectionClosedOK(None, None), logging.DEBUG, "Connection was closed normally, stopping the client."),
        (ConnectionClosedError(None, None), logging.ERROR, "Connection was terminated with an error."),
        (ConnectionClosed(None, None), logging.ERROR, "Connection was already closed."),
        (WebSocketException("broken"), logging.ERROR, "Connection is closed due to an unexpected WebSocket error."),
    ],
)
def test_listen_logs_websocket_exception_type(
    port_number: int,
    caplog: pytest.LogCaptureFixture,
    error: WebSocketException,
    level: int,
    message: str,
) -> None:
    async def scenario() -> None:
        client = WebSocketClient(port_number)
        connection = Mock()
        connection.recv = AsyncMock(side_effect=error)
        client._client = connection
        with pytest.raises(StopStreaming):
            async for _ in client.listen():
                pass

    caplog.set_level(logging.DEBUG, logger="streamdeck.websocket")
    asyncio.run(scenario())

    record = next(record for record in caplog.records if record.name == "streamdeck.websocket")
    assert record.levelno == level
    assert record.message == message
