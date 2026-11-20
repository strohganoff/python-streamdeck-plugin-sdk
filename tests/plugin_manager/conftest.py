from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, Mock, create_autospec

import pytest

from streamdeck.event_listener import EventListenerManager
from streamdeck.manager import PluginManager
from streamdeck.websocket import WebSocketTransport
from tests.test_utils.fake_event_factories import KeyDownEventFactory


async def _empty_event_stream() -> AsyncIterator[str]:
    if False:
        yield ""


if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    import pytest_mock

    from streamdeck.models import events


@pytest.fixture
def plugin_manager(port_number: int, plugin_registration_uuid: str) -> PluginManager:
    """Fixture that provides a configured instance of PluginManager for testing.

    Returns:
        PluginManager: An instance of PluginManager with test parameters.
    """
    plugin_uuid = "test-plugin-uuid"
    register_event = "registerPlugin"

    return PluginManager(
        port=port_number,
        plugin_uuid=plugin_uuid,
        plugin_registration_uuid=plugin_registration_uuid,
        register_event=register_event,
    )


@pytest.fixture(autouse=True)
def mock_streamdeck_logger(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep plugin manager tests independent of the user's log directory."""
    monkeypatch.setattr("streamdeck.manager.configure_streamdeck_logger", Mock())


@pytest.fixture
def patch_websocket_transport(monkeypatch: pytest.MonkeyPatch) -> Mock:
    """Provide the manager with a transport that performs no network I/O."""
    transport: Mock = create_autospec(WebSocketTransport, spec_set=True)
    transport.__aenter__.return_value = transport
    transport.__aexit__.return_value = False
    monkeypatch.setattr("streamdeck.manager.WebSocketTransport", lambda *args, **kwargs: transport)
    return transport


@pytest.fixture
def mock_command_sender(mocker: pytest_mock.MockerFixture) -> Mock:
    """Fixture that patches the StreamDeckCommandSender.

    Args:
        mocker: pytest-mock's mocker fixture.

    Returns:
        Mock: Mocked instance of StreamDeckCommandSender
    """
    mock_cmd_sender = Mock()
    mock_cmd_sender.send_action_registration = AsyncMock()
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
    mock_event_listener_manager.event_stream.return_value = _empty_event_stream()

    monkeypatch.setattr("streamdeck.manager.EventListenerManager", (lambda *args, **kwargs: mock_event_listener_manager))

    return mock_event_listener_manager



@pytest.fixture
def mock_event_listener_manager_with_fake_events(patch_event_listener_manager: Mock) -> tuple[Mock, list[events.EventBase]]:
    """Fixture that mocks the EventListenerManager and provides a list of fake event messages yielded by the mock manager.

    Returns:
        tuple: Mocked instance of EventListenerManager, and a list of fake event messages.
    """
    # Create a list of fake event messages, and convert them to json strings to be passed back by the listener manager.
    fake_event_messages: list[events.EventBase] = [
        KeyDownEventFactory.build(action="my-fake-action-uuid"),
    ]

    async def event_stream() -> AsyncIterator[str]:
        for event in fake_event_messages:
            yield event.model_dump_json()

    patch_event_listener_manager.event_stream.return_value = event_stream()

    return patch_event_listener_manager, fake_event_messages
