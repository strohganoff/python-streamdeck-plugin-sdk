from typing import cast
from unittest.mock import Mock

import pytest
import pytest_mock
from streamdeck.actions import Action
from streamdeck.manager import PluginManager
from streamdeck.models.events import DialRotate, EventBase, event_adapter

from tests.test_utils.fake_event_factories import DialRotateEventFactory


@pytest.fixture
def mock_websocket_client_with_event(patch_websocket_client: Mock) -> tuple[Mock, EventBase]:
    """Fixture that mocks the WebSocketClient and provides a fake DialRotateEvent message.

    Args:
        patch_websocket_client: Mocked instance of the patched WebSocketClient.

    Returns:
        tuple: Mocked instance of WebSocketClient, and a fake DialRotateEvent.
    """
    # Create a fake event message, and convert it to a json string to be passed back by the client.listen() method.
    fake_event_message: DialRotate = DialRotateEventFactory.build()
    patch_websocket_client.listen.return_value = [fake_event_message.model_dump_json()]

    return patch_websocket_client, fake_event_message



@pytest.fixture
def _spy_action_registry_get_action_handlers(
    mocker: pytest_mock.MockerFixture, plugin_manager: PluginManager
) -> None:
    """Fixture that wraps and spies on the get_action_handlers method of the action_registry.

    Args:
        mocker: pytest-mock's mocker fixture.
        plugin_manager: PluginManager fixture.

    Returns:
        None
    """
    mocker.spy(plugin_manager._action_registry, "get_action_handlers")


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
    assert len(plugin_manager._action_registry._plugin_actions) == 0

    action = Action("my-fake-action-uuid")
    plugin_manager.register_action(action)

    assert len(plugin_manager._action_registry._plugin_actions) == 1
    assert plugin_manager._action_registry._plugin_actions[0] == action


@pytest.mark.usefixtures("mock_websocket_client_with_event")
def test_plugin_manager_sends_registration_event(
    mock_command_sender: Mock, plugin_manager: PluginManager
):
    """Test that StreamDeckCommandSender.send_action_registration() method is called with correct arguments within the PluginManager.run() method."""
    plugin_manager.run()

    mock_command_sender.send_action_registration.assert_called_once_with(
        register_event=plugin_manager._register_event,
        plugin_registration_uuid=plugin_manager._registration_uuid,
    )


@pytest.mark.usefixtures("_spy_action_registry_get_action_handlers")
@pytest.mark.usefixtures("_spy_event_adapter_validate_json")
def test_plugin_manager_process_event(
    mock_websocket_client_with_event: tuple[Mock, EventBase], plugin_manager: PluginManager
):
    """Test that PluginManager processes events correctly, calling event_adapter.validate_json and action_registry.get_action_handlers."""
    mock_websocket_client, fake_event_message = mock_websocket_client_with_event

    plugin_manager.run()

    # First check that the WebSocketClient's listen() method was called.
    # This has been stubbed to return the fake_event_message's json string.
    mock_websocket_client.listen.assert_called_once()

    # Check that the event_adapter.validate_json method was called with the stub json string returned by listen().
    spied_event_adapter_validate_json = cast(Mock, event_adapter.validate_json)
    spied_event_adapter_validate_json.assert_called_once_with(fake_event_message.model_dump_json())
    # Check that the validate_json method returns the same event type model as the fake_event_message.
    assert spied_event_adapter_validate_json.spy_return == fake_event_message

    # Check that the action_registry.get_action_handlers method was called with the event name and action uuid.
    cast(Mock, plugin_manager._action_registry.get_action_handlers).assert_called_once_with(
        event_name=fake_event_message.event, event_action_uuid=fake_event_message.action
    )

