from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from unittest.mock import Mock, create_autospec

import pytest

from streamdeck.event_handlers.actions import Action
from streamdeck.event_handlers.injectables import InjectableHandlerParamStore
from streamdeck.event_handlers.scopes import Scope
from tests.test_utils.fake_event_factories import DidReceiveSettingsFactory, KeyDownEventFactory


if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from pydantic import JsonValue

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
    store.register("command_sender", lambda _event_data: mock_command_sender)
    event_data = Mock()
    with_sender = store.resolve_for_handler(handler_with_sender, event_data)
    without_sender = store.resolve_for_handler(handler_without_sender, event_data)

    assert with_sender == {"command_sender": mock_command_sender}
    assert without_sender == {}


def test_injectable_param_store_resolves_multiple_named_values() -> None:
    """The store resolves multiple named values and ignores unprovided names."""
    command_sender = Mock()
    event_snapshot = object()
    store = InjectableHandlerParamStore()
    store.register("command_sender", lambda _event_data: command_sender)
    store.register("event_snapshot", lambda _event_data: event_snapshot)

    injected_params = store.resolve(("command_sender", "event_snapshot", "unused"), Mock())

    assert injected_params == {
        "command_sender": command_sender,
        "event_snapshot": event_snapshot,
    }


def test_manager_validates_and_resolves_custom_store_value(plugin_manager: PluginManager) -> None:
    """Registration and dispatch use the same manager-owned injectable names."""
    provided_value = object()
    plugin_manager._injectable_handler_param_store = InjectableHandlerParamStore()
    plugin_manager._injectable_handler_param_store.register(
        "extension_value",
        lambda _event_data: provided_value,
    )

    def handler(event_data: events.EventBase, extension_value: object) -> None:
        pass

    mock_handler = create_autospec(handler, spec_set=True)
    action = Action("test.action")
    action.on("applicationDidLaunch")(mock_handler)

    plugin_manager.register_action(action)
    plugin_manager._validate_registered_handler_signatures()

    event_data = Mock(event="applicationDidLaunch")
    asyncio.run(plugin_manager._dispatch_event(event_data))

    mock_handler.assert_called_once_with(event_data, extension_value=provided_value)


def test_manager_rejects_required_param_without_provider(plugin_manager: PluginManager) -> None:
    """Required handler parameters must have a provider in the manager's store."""
    def handler(event_data: events.EventBase, missing_value: object) -> None:
        pass

    action = Action("test.action")
    action.on("applicationDidLaunch")(handler)
    plugin_manager.register_action(action)
    plugin_manager._injectable_handler_param_store.register(
        "command_sender",
        lambda _event_data: Mock(),
    )

    with pytest.raises(TypeError, match="Invalid event handler signature"):
        plugin_manager._injectable_handler_param_store.validate_handler_signature(
            handler,
            (Scope.PLUGIN,),
            "applicationDidLaunch",
        )


def test_dispatch_awaits_async_handlers_in_registration_sequence(plugin_manager: PluginManager) -> None:
    """Async handlers finish before the next matching handler begins."""
    calls: list[str] = []

    action = Action("test.action")

    @action.on("applicationDidLaunch")
    async def async_handler(event_data: events.EventBase) -> None:
        calls.append("async-start")
        await asyncio.sleep(0)
        calls.append("async-end")

    @action.on("applicationDidLaunch")
    def sync_handler(event_data: events.EventBase) -> None:
        calls.append("sync")

    plugin_manager.register_action(action)
    plugin_manager._handlers_registry.get_event_handlers = lambda **_kwargs: [async_handler, sync_handler]
    asyncio.run(plugin_manager._dispatch_event(Mock(event="applicationDidLaunch")))

    assert calls == ["async-start", "async-end", "sync"]


@pytest.mark.usefixtures("patch_websocket_transport")
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

    NOTE: The WebSocketTransport is mocked so as to be essentially ignored in this test.

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
    asyncio.run(plugin_manager.run())

    # Ensure that mocked event handlers were called with the correct params, binding the `command_sender` parameter if defined in the handler's signature.
    mock_event_handler_without_cmd_sender.assert_called_once_with(fake_event_message)
    mock_event_handler_with_cmd_sender.assert_called_once_with(fake_event_message, mock_command_sender)


def test_handler_can_await_settings_before_response_dispatch(
    patch_websocket_transport: Mock,
    patch_event_listener_manager: Mock,
    plugin_manager: PluginManager,
) -> None:
    async def scenario() -> None:
        key_down = KeyDownEventFactory.build()
        action = Action(key_down.action)
        responses: asyncio.Queue[events.DidReceiveSettings] = asyncio.Queue()
        handled: list[tuple[str, events.DidReceiveSettings]] = []

        async def event_stream() -> AsyncIterator[str]:
            yield key_down.model_dump_json()
            response = await responses.get()
            yield response.model_dump_json()

        async def send(data: dict[str, JsonValue]) -> None:
            if data["event"] == "getSettings":
                assert data["context"] == key_down.context
                request_id = data["id"]
                assert isinstance(request_id, str)
                responses.put_nowait(DidReceiveSettingsFactory.build(
                    id=request_id,
                    action=key_down.action,
                    context=key_down.context,
                    device=key_down.device,
                ))

        @action.on("keyDown")
        async def request_settings(
            event_data: events.KeyDown,
            command_sender: StreamDeckCommandSender,
        ) -> None:
            response = await command_sender.get_settings(event_data.context, wait_for_response=True)
            handled.append(("request", response))

        @action.on("didReceiveSettings")
        def receive_settings(event_data: events.DidReceiveSettings) -> None:
            handled.append(("dispatch", event_data))

        patch_event_listener_manager.event_stream.return_value = event_stream()
        patch_websocket_transport.send_event.side_effect = send
        plugin_manager.register_action(action)
        await asyncio.wait_for(plugin_manager.run(), timeout=1)

        assert [step for step, _ in handled] == ["request", "dispatch"]
        assert handled[0][1] is handled[1][1]

    asyncio.run(scenario())
