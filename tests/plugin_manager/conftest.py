from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import Mock, create_autospec

import pytest
from streamdeck.event_listener import EventListenerManager
from streamdeck.manager import PluginManager
from streamdeck.websocket import WebSocketClient

from tests.test_utils.fake_event_factories import KeyDownEventFactory


if TYPE_CHECKING:
    import pytest_mock
    from streamdeck.models import events
    from streamdeck.models.events.base import LiteralStrGenericAlias


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
        Mock: Mocked instance of WebSocketClient
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



@pytest.fixture
def patch_event_listener_manager(monkeypatch: pytest.MonkeyPatch) -> Mock:
    """Fixture that uses pytest's MonkeyPatch to mock EventListenerManager for the PluginManager run method.

    The mocked EventListenerManager can be given fake event messages to yield when event_stream() is called:
      ```patch_event_listener_manager.event_stream.return_value = [fake_event_json1, fake_event_json2, ...]```

    Args:
        monkeypatch: pytest's monkeypatch fixture.

    Returns:
        Mock: Mocked instance of EventListenerManager
    """
    mock_event_listener_manager: Mock = create_autospec(EventListenerManager, spec_set=True)

    monkeypatch.setattr("streamdeck.manager.EventListenerManager", (lambda *args, **kwargs: mock_event_listener_manager))

    return mock_event_listener_manager



@pytest.fixture
def mock_event_listener_manager_with_fake_events(patch_event_listener_manager: Mock) -> tuple[Mock, list[events.EventBase]]:
    """Fixture that mocks the EventListenerManager and provides a list of fake event messages yielded by the mock manager.

    Returns:
        tuple: Mocked instance of EventListenerManager, and a list of fake event messages.
    """
    print("MOCK EVENT LISTENER MANAGER")
    # Create a list of fake event messages, and convert them to json strings to be passed back by the client.listen() method.
    fake_event_messages: list[events.EventBase[LiteralStrGenericAlias]] = [
        KeyDownEventFactory.build(action="my-fake-action-uuid"),
    ]

    patch_event_listener_manager.event_stream.return_value = [event.model_dump_json() for event in fake_event_messages]

    return patch_event_listener_manager, fake_event_messages
