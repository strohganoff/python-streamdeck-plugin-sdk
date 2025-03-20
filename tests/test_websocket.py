from __future__ import annotations

import json
from functools import partial
from typing import TYPE_CHECKING, Any
from unittest.mock import Mock

import pytest
from streamdeck.event_listener import StopStreaming
from streamdeck.websocket import WebSocketClient
from websockets import (
    ConnectionClosed,
    ConnectionClosedError,
    ConnectionClosedOK,
    InvalidHeader,
    WebSocketException,
)


if TYPE_CHECKING:
    from pytest_mock import MockerFixture


@pytest.fixture
def mock_connection() -> Mock:
    """Fixture to mock the ClientConnection object returned by websockets.sync.client.connect."""
    return Mock()


@pytest.fixture
def patched_connect(mocker: MockerFixture, mock_connection: Mock) -> Mock:
    """Fixture to mock the ClientConnection object returned by websockets.sync.client.connect."""
    return mocker.patch("streamdeck.websocket.connect", return_value=mock_connection)


def test_initialization_calls_connect_correctly(
    patched_connect: Mock, mock_connection: Mock, port_number: int
) -> None:
    """Test that WebSocketClient initializes correctly by calling the connect function with the appropriate URI."""
    with WebSocketClient(port=port_number) as client:
        # Assert that 'connect' was called once with the correct URI.
        patched_connect.assert_called_once_with(uri=f"ws://localhost:{port_number}")

        # Assert that the client's _client attribute is the mocked connection
        assert client._client == mock_connection


@pytest.mark.usefixtures("patched_connect")
def test_send_event_serializes_and_sends(mock_connection: Mock, port_number: int) -> None:
    """Test that the send_event method corrently serializes the data to JSON and sends it via the websocket connection."""
    with WebSocketClient(port=port_number) as client:
        fake_data = {"event": "test_event", "payload": {"key": "value"}}
        client.send_event(fake_data)

    # Assert that the 'send' method was called once with the serialized data.
    expected_message = json.dumps(fake_data)
    mock_connection.send.assert_called_once_with(message=expected_message)


@pytest.mark.usefixtures("patched_connect")
def test_listen_yields_messages(mock_connection: Mock, port_number: int) -> None:
    """Test that listen yields messages from the WebSocket connection."""
    # Set up the mocked connection to return messages until closing
    expected_results = ["message1", b"message2", "message3"]
    mock_connection.recv.side_effect = expected_results

    with WebSocketClient(port=port_number) as client:
        actual_messages: list[Any] = []
        for i, msg in enumerate(client.listen()):
            actual_messages.append(msg)
            if i == 2:
                break

    assert actual_messages == expected_results


@pytest.mark.parametrize(
    "exception_class",
    [
        partial(ConnectionClosedOK, None, None),
        partial(ConnectionClosedError, None, None),
        partial(InvalidHeader, "header-name", None),
        partial(ConnectionClosed, None, None),
        WebSocketException,
    ],
)
@pytest.mark.usefixtures("patched_connect")
def test_listen_raises_StopStreaming_from_WebSocketException(
    mock_connection: Mock, port_number: int, exception_class: type[WebSocketException]
) -> None:
    """Test that listen raises a StopStreaming exception when a WebSocketException is raised."""
    # Set up the mocked connection to return messages until closing
    mock_connection.recv.side_effect = ["message1", b"message2", exception_class()]

    # This should raise a StopStreaming exception when any WebSocketException is raised
    with WebSocketClient(port=port_number) as client, pytest.raises(StopStreaming):
        for _ in client.listen():
            pass
