from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import Mock, create_autospec

import pytest
from streamdeck.actions import Action


if TYPE_CHECKING:
    from functools import partial

    from streamdeck.command_sender import StreamDeckCommandSender
    from streamdeck.manager import PluginManager
    from streamdeck.models import events
    from streamdeck.models.events.base import LiteralStrGenericAlias
    from streamdeck.types import (
        EventHandlerBasicFunc,
        EventHandlerFunc,
    )



def create_event_handler(include_command_sender_param: bool = False) -> EventHandlerFunc[events.EventBase]:
    """Create a dummy event handler function that matches the EventHandlerFunc TypeAlias.

    Args:
        include_command_sender_param (bool, optional): Whether to include the `command_sender` parameter in the handler. Defaults to False.

    Returns:
        Callable[[events.EventBase], None] | Callable[[events.EventBase, StreamDeckCommandSender], None]: A dummy event handler function.
    """
    if not include_command_sender_param:
        def dummy_handler_without_cmd_sender(event_data: events.EventBase[LiteralStrGenericAlias]) -> None:
            """Dummy event handler function that matches the EventHandlerFunc TypeAlias without `command_sender` param."""

        return dummy_handler_without_cmd_sender

    def dummy_handler_with_cmd_sender(event_data: events.EventBase[LiteralStrGenericAlias], command_sender: StreamDeckCommandSender) -> None:
        """Dummy event handler function that matches the EventHandlerFunc TypeAlias with `command_sender` param."""

    return dummy_handler_with_cmd_sender


@pytest.fixture(params=[True, False])
def mock_event_handler(request: pytest.FixtureRequest) -> Mock:
    include_command_sender_param: bool = request.param
    dummy_handler: EventHandlerFunc[events.EventBase[LiteralStrGenericAlias]] = create_event_handler(include_command_sender_param)

    return create_autospec(dummy_handler, spec_set=True)



def test_inject_command_sender_func(
    plugin_manager: PluginManager,
    mock_event_handler: Mock,
) -> None:
    """Test that the command_sender is injected into the handler."""
    mock_command_sender = Mock()
    result_handler: EventHandlerBasicFunc[events.EventBase[LiteralStrGenericAlias]] = plugin_manager._inject_command_sender(mock_event_handler, mock_command_sender)

    resulting_handler_params = inspect.signature(result_handler).parameters

    # If this condition is true, then the `result_handler` is a partial function.
    if "command_sender" in resulting_handler_params:

        # Check that the `result_handler` is not the same as the original `mock_event_handler`.
        assert result_handler != mock_event_handler

        # Check that the `command_sender` parameter is bound to the correct value.
        resulting_handler_bound_kwargs: dict[str, Any] = cast("partial[Any]", result_handler).keywords
        assert resulting_handler_bound_kwargs["command_sender"] == mock_command_sender

    # If there isn't a `command_sender` parameter, then the `result_handler` is the original handler unaltered.
    else:
        assert result_handler == mock_event_handler


@pytest.mark.usefixtures("patch_websocket_client")
def test_run_manager_events_handled_with_correct_params(
    mock_event_listener_manager_with_fake_events: tuple[Mock, list[events.EventBase[LiteralStrGenericAlias]]],
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
