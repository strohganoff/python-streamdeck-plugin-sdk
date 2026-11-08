from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import Mock, create_autospec

import pytest
from streamdeck.event_handlers.actions import Action
from streamdeck.event_handlers.injectables import InjectableHandlerParamStore


if TYPE_CHECKING:
    from streamdeck.command_sender import StreamDeckCommandSender
    from streamdeck.event_handlers.protocol import EventHandlerFunc
    from streamdeck.manager import PluginManager
    from streamdeck.models import events



def create_event_handler(include_command_sender_param: bool = False) -> EventHandlerFunc:
    """Create a dummy event handler function that matches the EventHandlerFunc TypeAlias.

    Args:
        include_command_sender_param (bool, optional): Whether to include the `command_sender` parameter in the handler. Defaults to False.

    Returns:
        Callable[[events.EventBase], None] | Callable[[events.EventBase, StreamDeckCommandSender], None]: A dummy event handler function.
    """
    if not include_command_sender_param:
        def dummy_handler_without_cmd_sender(event_data: events.EventBase) -> None:
            """Dummy event handler function that matches the EventHandlerFunc TypeAlias without `command_sender` param."""

        return dummy_handler_without_cmd_sender

    def dummy_handler_with_cmd_sender(event_data: events.EventBase, command_sender: StreamDeckCommandSender) -> None:
        """Dummy event handler function that matches the EventHandlerFunc TypeAlias with `command_sender` param."""

    return dummy_handler_with_cmd_sender


def test_injectable_param_store_resolves_only_declared_params() -> None:
    """Resolve SDK values by name and provide only parameters requested by a handler."""
    mock_command_sender = Mock()
    handler_with_sender = create_event_handler(include_command_sender_param=True)
    handler_without_sender = create_event_handler(include_command_sender_param=False)

    store = InjectableHandlerParamStore()
    store.set_value("command_sender", mock_command_sender)
    with_sender = store.resolve_for_handler(handler_with_sender)
    without_sender = store.resolve_for_handler(handler_without_sender)

    assert with_sender == {"command_sender": mock_command_sender}
    assert without_sender == {}


def test_injectable_param_store_resolves_multiple_named_values() -> None:
    """The store resolves multiple named values and ignores unprovided names."""
    command_sender = Mock()
    event_snapshot = object()
    store = InjectableHandlerParamStore()
    store.set_value("command_sender", command_sender)
    store.set_value("event_snapshot", event_snapshot)

    injected_params = store.resolve(("command_sender", "event_snapshot", "unused"))

    assert injected_params == {
        "command_sender": command_sender,
        "event_snapshot": event_snapshot,
    }


def test_manager_validates_and_resolves_custom_store_value(plugin_manager: PluginManager) -> None:
    """Registration and dispatch use the same manager-owned injectable names."""
    provided_value = object()
    plugin_manager._injectable_handler_param_store = InjectableHandlerParamStore()
    plugin_manager._injectable_handler_param_store.set_value("extension_value", provided_value)

    def handler(event_data: events.EventBase, extension_value: object) -> None:
        pass

    mock_handler = create_autospec(handler, spec_set=True)
    action = Action("test.action")
    action.on("applicationDidLaunch")(mock_handler)

    plugin_manager.register_action(action)
    plugin_manager._validate_registered_handler_signatures()

    event_data = Mock(event="applicationDidLaunch")
    plugin_manager._dispatch_event(event_data)

    mock_handler.assert_called_once_with(event_data, extension_value=provided_value)


def test_manager_rejects_required_param_without_provider(plugin_manager: PluginManager) -> None:
    """Required handler parameters must have a provider in the manager's store."""
    def handler(event_data: events.EventBase, missing_value: object) -> None:
        pass

    action = Action("test.action")
    action.on("applicationDidLaunch")(handler)
    plugin_manager.register_action(action)
    plugin_manager._injectable_handler_param_store.set_value("command_sender", Mock())

    with pytest.raises(TypeError, match="Invalid event handler signature"):
        plugin_manager._injectable_handler_param_store.validate_handler_signature(handler)


@pytest.mark.usefixtures("patch_websocket_client")
def test_run_manager_events_handled_with_correct_params(
    mock_event_listener_manager_with_fake_events: tuple[Mock, list[events.EventBase]],
    plugin_manager: PluginManager,
    mock_command_sender: Mock,
) -> None:
    """Test that the PluginManager runs and triggers event handlers with the correct parameter binding.

    This test will:
      - Register an action with the PluginManager.
      - Create and register mock event handlers with and without the `command_sender` parameter.
      - Run the PluginManager and let it process the fake event messages generated by the mocked EventListenerManager.
      - Ensure that mocked event handlers were called with the correct params,
          binding the `command_sender` parameter if defined in the handler's signature.

    NOTE: The WebSocketClient is mocked so as to be essentially ignored in this test.

    Args:
        mock_event_listener_manager_with_fake_events (tuple[Mock, list[events.EventBase]]): Mocked instance of EventListenerManager, and a list of fake event messages it will yield.
        plugin_manager (PluginManager): Instance of PluginManager with test parameters.
        mock_command_sender (Mock): Patched instance of StreamDeckCommandSender. Used here to ensure that the `command_sender` parameter is bound correctly.
    """
    # As of now, fake_event_messages is a list of one KeyDown event. If this changes, I'll need to update this test.
    fake_event_message: events.KeyDown = mock_event_listener_manager_with_fake_events[1][0]

    action = Action(fake_event_message.action)

    # Create a mock event handler with the `command_sender` parameter and register it with the action for an event type.
    mock_event_handler_with_cmd_sender: Mock = create_autospec(create_event_handler(include_command_sender_param=True), spec_set=True)
    action.on("keyDown")(mock_event_handler_with_cmd_sender)

    # Create a mock event handler without the `command_sender` parameter and register it with the action for an event type.
    mock_event_handler_without_cmd_sender: Mock = create_autospec(create_event_handler(include_command_sender_param=False), spec_set=True)
    action.on("keyDown")(mock_event_handler_without_cmd_sender)

    plugin_manager.register_action(action)

    # Run the PluginManager and let it process the fake event messages generated by the mocked EventListenerManager.
    # Since the EventListenerManager.event_stream() method is mocked to return a finite list of fake event messages, it will stop after yielding all of them rather than running indefinitely.
    plugin_manager.run()

    # Ensure that mocked event handlers were called with the correct params, binding the `command_sender` parameter if defined in the handler's signature.
    mock_event_handler_without_cmd_sender.assert_called_once_with(fake_event_message)
    mock_event_handler_with_cmd_sender.assert_called_once_with(fake_event_message, mock_command_sender)
