from typing import cast
from unittest.mock import MagicMock, Mock

import pytest
import pytest_mock
from polyfactory.factories.pydantic_factory import ModelFactory
from streamdeck.actions import Action
from streamdeck.manager import PluginManager
from streamdeck.models.events import DialRotateEvent, EventBase, event_adapter
from streamdeck.websocket import WebSocketClient


class DialRotateEventFactory(ModelFactory[DialRotateEvent]):
    """Polyfactory factory for creating a fake event message based on our Pydantic model."""


@pytest.fixture
def plugin_manager(port_number: int) -> PluginManager:
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
        register_event=register_event,
        info=info
    )


@pytest.fixture
def patch_websocket_client(monkeypatch: pytest.MonkeyPatch) -> tuple[MagicMock, EventBase]:
    """Fixture that uses pytest's MonkeyPatch to mock WebSocketClient and StreamDeckCommandSender for the PluginManager run method.

    Args:
        monkeypatch: pytest's monkeypatch fixture.

    Returns:
        tuple: Mocked instance of WebSocketClient, and a fake DialRotateEvent.
    """

    mock_websocket_client = MagicMock(spec=WebSocketClient)

    mock_websocket_client.__enter__.return_value = mock_websocket_client

    # Create a fake event message, and convert it to a json string to be passed back by the client.listen_forever() method.
    fake_event_message = DialRotateEventFactory.build()
    mock_websocket_client.listen_forever.return_value = [fake_event_message.model_dump_json()]

    monkeypatch.setattr("streamdeck.manager.WebSocketClient", lambda port: mock_websocket_client)

    return mock_websocket_client, fake_event_message


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
def _spy_action_registry_get_action_handlers(mocker: pytest_mock.MockerFixture, plugin_manager: PluginManager) -> None:
    """Fixture that wraps and spies on the get_action_handlers method of the action_registry.

    Args:
        mocker: pytest-mock's mocker fixture.
        plugin_manager: PluginManager fixture.

    Returns:
        None
    """
    mocker.spy(plugin_manager._registry, "get_action_handlers")


@pytest.fixture
def _spy_event_adapter_validate_json(mocker: pytest_mock.MockerFixture) -> None:
    """Fixture that wraps and spies on the event_adapter.validate_json method.

    Args:
        mocker: pytest-mock's mocker fixture.

    Returns:
        None
    """
    mocker.spy(event_adapter, "validate_json")


def test_plugin_manager_register_action(plugin_manager: PluginManager):
    """Test that an action can be registered in the PluginManager."""
    assert len(plugin_manager._registry._plugin_actions) == 0

    action = Action("my-fake-action-uuid")
    plugin_manager.register_action(action)

    assert len(plugin_manager._registry._plugin_actions) == 1
    assert plugin_manager._registry._plugin_actions[0] == action


@pytest.mark.usefixtures("patch_websocket_client")
def test_plugin_manager_sends_registration_event(mock_command_sender: Mock, plugin_manager: PluginManager):
    """Test that StreamDeckCommandSender.send_action_registration() method is called with correct arguments within the PluginManager.run() method."""
    plugin_manager.run()

    mock_command_sender.send_action_registration.assert_called_once_with(
        register_event=plugin_manager._register_event,
        plugin_uuid=plugin_manager.uuid,
    )


@pytest.mark.usefixtures("_spy_action_registry_get_action_handlers")
@pytest.mark.usefixtures("_spy_event_adapter_validate_json")
def test_plugin_manager_process_event(patch_websocket_client: tuple[MagicMock, EventBase], plugin_manager: PluginManager):
    """Test that PluginManager processes events correctly, calling event_adapter.validate_json and action_registry.get_action_handlers."""
    mock_websocket_client, fake_event_message = patch_websocket_client

    plugin_manager.run()

    mock_websocket_client.listen_forever.assert_called_once()

    spied_event_adapter_validate_json = cast(Mock, event_adapter.validate_json)
    spied_event_adapter_validate_json.assert_called_once_with(fake_event_message.model_dump_json())
    assert spied_event_adapter_validate_json.spy_return == fake_event_message

    cast(Mock, plugin_manager._registry.get_action_handlers).assert_called_once_with(fake_event_message.event)