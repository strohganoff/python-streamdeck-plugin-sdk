from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest
from streamdeck.websocket import WebSocketClient
from websockets import ConnectionClosedOK, WebSocketException


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


def test_initialization_calls_connect_correctly(patched_connect: Mock, mock_connection: Mock, port_number: int):
    """Test that WebSocketClient initializes correctly by calling the connect function with the appropriate URI."""
    with WebSocketClient(port=port_number) as client:
        # Assert that 'connect' was called once with the correct URI.
        patched_connect.assert_called_once_with(uri=f"ws://localhost:{port_number}")

        # Assert that the client's _client attribute is the mocked connection
        assert client._client == mock_connection


@pytest.mark.usefixtures("patched_connect")
def test_send_event_serializes_and_sends(mock_connection: Mock, port_number: int):
    """Test that the send_event method corrently serializes the data to JSON and sends it via the websocket connection."""
    with WebSocketClient(port=port_number) as client:
        fake_data = {"event": "test_event", "payload": {"key": "value"}}
        client.send_event(fake_data)

    # Assert that the 'send' method was called once with the serialized data.
    expected_message = json.dumps(fake_data)
    mock_connection.send.assert_called_once_with(message=expected_message)


@pytest.mark.usefixtures("patched_connect")
def test_listen_forever_yields_messages(mock_connection: Mock, port_number: int):
    """Test that listen_forever yields messages from the WebSocket connection."""
    # Set up the mocked connection to return messages until closing
    mock_connection.recv.side_effect = ["message1", b"message2", WebSocketException()]

    with WebSocketClient(port=port_number) as client:
        messages = list(client.listen_forever())

    assert messages == ["message1", b"message2"]