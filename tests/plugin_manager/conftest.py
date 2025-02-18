from __future__ import annotations

import uuid
from unittest.mock import Mock, create_autospec

import pytest
from streamdeck.manager import PluginManager
from streamdeck.websocket import WebSocketClient


@pytest.fixture
def plugin_manager(port_number: int, plugin_registration_uuid: str) -> PluginManager:
    """Fixture that provides a configured instance of PluginManager for testing.

    Returns:
        PluginManager: An instance of PluginManager with test parameters.
    """
    plugin_uuid = "test-plugin-uuid"
    register_event = "registerPlugin"
    info = {"some": "info"}

    return PluginManager(
        port=port_number,
        plugin_uuid=plugin_uuid,
        plugin_registration_uuid=plugin_registration_uuid,
        register_event=register_event,
        info=info,
    )


@pytest.fixture
def patch_websocket_client(monkeypatch: pytest.MonkeyPatch) -> Mock:
    """Fixture that uses pytest's MonkeyPatch to mock WebSocketClient for the PluginManager run method.

    The mocked WebSocketClient can be given fake event messages to yield when listen() is called:
      ```patch_websocket_client.listen.return_value = [fake_event_json1, fake_event_json2, ...]```

    Args:
        monkeypatch: pytest's monkeypatch fixture.

    Returns:
    """
    mock_websocket_client: Mock = create_autospec(WebSocketClient, spec_set=True)
    mock_websocket_client.__enter__.return_value = mock_websocket_client

    monkeypatch.setattr("streamdeck.manager.WebSocketClient", (lambda *args, **kwargs: mock_websocket_client))

    return mock_websocket_client


@pytest.fixture
def mock_command_sender(mocker: pytest_mock.MockerFixture) -> Mock:
    """Fixture that patches the StreamDeckCommandSender.

    Args:
        mocker: pytest-mock's mocker fixture.

    Returns:
        Mock: Mocked instance of StreamDeckCommandSender
    """
    mock_cmd_sender = Mock()
    mocker.patch("streamdeck.manager.StreamDeckCommandSender", return_value=mock_cmd_sender)
    return mock_cmd_sender
