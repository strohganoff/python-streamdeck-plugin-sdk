from typing import cast
from unittest.mock import Mock

import pytest
import pytest_mock
from streamdeck.actions import Action
from streamdeck.manager import EventAdapter, PluginManager
from streamdeck.models.events import (  #, event_adapter
    DEFAULT_EVENT_MODELS,
    DEFAULT_EVENT_NAMES,
    EventBase,
)
from streamdeck.models.events.base import LiteralStrGenericAlias


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
    mocker.spy(EventAdapter, "validate_json")


def test_plugin_manager_register_action(plugin_manager: PluginManager) -> None:
    """Test that an action can be registered in the PluginManager."""
    assert len(plugin_manager._action_registry._plugin_actions) == 0

    action = Action("my-fake-action-uuid")
    plugin_manager.register_action(action)

    assert len(plugin_manager._action_registry._plugin_actions) == 1
    assert plugin_manager._action_registry._plugin_actions[0] == action


def test_plugin_manager_register_event_listener(plugin_manager: PluginManager) -> None:
    """Test that an event listener can be registered in the PluginManager."""
    mock_event_model_class = Mock(get_model_event_names=lambda: ["fake_event_name"])
    listener = Mock(event_models=[mock_event_model_class])

    assert len(plugin_manager._event_listener_manager.listeners_lookup_by_thread) == 0

    plugin_manager.register_event_listener(listener)

    # Validate that the PluginManager's EventListenerManager has the listener properly registered.
    assert len(plugin_manager._event_listener_manager.listeners_lookup_by_thread) == 1
    assert next(iter(plugin_manager._event_listener_manager.listeners_lookup_by_thread.values())) == listener

    # Validate that the PluginManager's EventAdapter has the event model class properly registered.
    assert len(plugin_manager._event_adapter._models) == len(DEFAULT_EVENT_MODELS) + 1
    assert mock_event_model_class in plugin_manager._event_adapter._models
    # Also validate that the event name is in the set of registered event names.
    assert len(plugin_manager._event_adapter._event_names) == len(DEFAULT_EVENT_NAMES) + 1
    assert "fake_event_name" in plugin_manager._event_adapter._event_names


@pytest.mark.usefixtures("patch_websocket_client", "patch_event_listener_manager")
def test_plugin_manager_sends_registration_event(
    mock_command_sender: Mock,
    plugin_manager: PluginManager,
) -> None:
    """Test that StreamDeckCommandSender.send_action_registration() method is called with correct arguments within the PluginManager.run() method.

    When the PluginManager.run() method is called, it should register the plugin with the StreamDeck software by sending an action registration event via the StreamDeckCommandSender instance.

    NOTE: The WebSocketClient and EventListenerManager are mocked so as to be essentially ignored in this test.
    """
    plugin_manager.run()

    mock_command_sender.send_action_registration.assert_called_once_with(
        register_event=plugin_manager._register_event,
    )


def test_plugin_manager_adds_websocket_event_listener(
    patch_event_listener_manager: Mock,
    patch_websocket_client: Mock,
    plugin_manager: PluginManager,  # This fixture must come after patch_event_listener_manager to ensure monkeypatching occurs.
) -> None:
    """Test that the PluginManager adds the WebSocketClient as an event listener.

    The PluginManager.run() method should add the WebSocketClient as an event listener to the EventListenerManager.

    Args:
        patch_event_listener_manager (Mock): Mocked instance of EventListenerManager.
            Patched by the fixture, and used here to check if this instance's .add_listener() method was called with the appropriate arguments.
        patch_websocket_client (Mock): Mocked instance of WebSocketClient.
            Patched by the fixture, and used here to check if this instance was passed to the EventListenerManager.add_listener() method as an argument.
        plugin_manager (PluginManager): PluginManager fixture
    """
    plugin_manager.run()

    patch_event_listener_manager.add_listener.assert_called_once_with(patch_websocket_client)


@pytest.mark.integration
@pytest.mark.usefixtures("patch_websocket_client")
def test_plugin_manager_process_event(
    mock_event_listener_manager_with_fake_events: tuple[Mock, list[EventBase[LiteralStrGenericAlias]]],
    _spy_action_registry_get_action_handlers: None,  # This fixture must come after mock_event_listener_manager_with_fake_events to ensure monkeypatching occurs.
    _spy_event_adapter_validate_json: None,  # This fixture must come after mock_event_listener_manager_with_fake_events to ensure monkeypatching occurs.
    plugin_manager: PluginManager,   # This fixture must come after patch_event_listener_manager and spy-fixtures to ensure things are mocked and spied correctly.
) -> None:
    """Test that PluginManager processes events correctly, calling event_adapter.validate_json and action_registry.get_action_handlers."""
    mock_event_listener_mgr, fake_event_messages = mock_event_listener_manager_with_fake_events
    fake_event_message = fake_event_messages[0]

    plugin_manager.run()

    # First check that the EventListenerManager's event_stream() method was called.
    # This has been stubbed to return the fake_event_message's json string.
    mock_event_listener_mgr.event_stream.assert_called_once()

    # Check that the event_adapter.validate_json method was called with the stub json string returned by listen().
    spied_event_adapter__validate_json = cast("Mock", EventAdapter.validate_json)
    # Since this is an instance method, the first argument is the instance itself.
    spied_event_adapter__validate_json.assert_called_once_with(plugin_manager._event_adapter, fake_event_message.model_dump_json())
    # Check that the validate_json method returns the same event type model as the fake_event_message.
    assert spied_event_adapter__validate_json.spy_return == fake_event_message

    # Check that the action_registry.get_action_handlers method was called with the event name and action uuid.
    spied_action_registry__get_action_handlers = cast("Mock", plugin_manager._action_registry.get_action_handlers)
    spied_action_registry__get_action_handlers.assert_called_once_with(
        event_name=fake_event_message.event, event_action_uuid=fake_event_message.action
    )

