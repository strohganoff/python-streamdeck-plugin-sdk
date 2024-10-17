from __future__ import annotations

from unittest.mock import Mock

import pytest
from streamdeck.command_sender import StreamDeckCommandSender
from streamdeck.websocket import WebSocketClient


@pytest.fixture
def mock_client() -> Mock:
    """Fixture to mock the WebSocketClient."""
    return Mock(spec=WebSocketClient)


@pytest.fixture
def command_sender(mock_client: Mock) -> StreamDeckCommandSender:
    """Fixture to provide an instance of StreamDeckCommandSender with a mocked client."""
    return StreamDeckCommandSender(client=mock_client)


@pytest.mark.parametrize(
    ("method_name", "context", "extra_args", "expected_event", "expected_payload"),
    [
        (
            "get_global_settings",
            "fake_context",
            {},
            "getGlobalSettings",
            {}
        ),
        (
            "get_settings",
            "fake_context",
            {},
            "getSettings",
            {}
        ),
        (
            "log_message",
            "fake_context",
            {"message": "fake log message..."},
            "logMessage",
            {"payload": {"message": "fake log message..."}}
        ),
        (
            "open_url",
            "fake_context",
            {"url": "http://example.com"},
            "openUrl",
            {"payload": {"url": "http://example.com"}}
        ),
        (
            "show_alert",
            "fake_context",
            {},
            "showAlert",
            {}
        ),
        (
            "show_ok",
            "fake_context",
            {},
            "showOk",
            {}
        ),
        (
            "send_to_plugin",
            "fake_context",
            {"action": "fake_action", "payload": {"key": "value"}},
            "sendToPlugin",
            {"action": "fake_action", "payload": {"key": "value"}},
        ),
        (
            "send_to_property_inspector",
            "fake_context",
            {"payload": {"key": "value"}},
            "sendToPropertyInspector",
            {"payload": {"key": "value"}},
        ),
        (
            "set_feedback",
            "fake_context",
            {"payload": {"key": "value"}},
            "setFeedback",
            {"payload": {"key": "value"}},
        ),
        (
            "set_feedback_layout",
            "fake_context",
            {"layout": "fake layout"},
            "setFeedbackLayout",
            {"payload": {"layout": "fake layout"}},
        ),
        (
            "set_image",
            "fake_context",
            {"state": "fake_state", "image": "fake-base64encodedstring", "target": "hardware"},
            "setImage",
            {"payload": {"state": "fake_state", "image": "fake-base64encodedstring", "target": 1}},
        ),
        (
            "set_title",
            "fake_context",
            {"state": "fake_state", "target": "fake_title", "title": "fake_title"},
            "setTitle",
            {"payload": {"state": "fake_state", "target": "fake_title", "title": "fake_title"}},
        ),
        (
            "set_trigger_description",
            "fake_context",
            {"rotate": "fake rotate description", "push": "fake push description", "touch": "fake touch description", "long_touch": "fake long touch description"},
            "setTriggerDescription",
            {"payload": {"rotate": "fake rotate description", "push": "fake push description", "touch": "fake touch description", "longTouch": "fake long touch description"}},
        ),
        (
            "set_global_settings",
            "fake_context",
            {"payload": {"key": "value"}},
            "setGlobalSettings",
            {"payload": {"key": "value"}},
        ),
        (
            "set_settings",
            "fake_context",
            {"payload": {"key": "value"}},
            "setSettings",
            {"payload": {"key": "value"}},
        ),
        (
            "set_state",
            "fake_context",
            {"state": 1},
            "setState",
            {"payload": {"state": 1}},
        ),
        (
            "switch_to_profile",
            "fake_context",
            {"device": "fake device", "profile": "fake profile", "page": 4},
            "switchToProfile",
            {"device": "fake device", "payload": {"profile": "fake profile", "page": 4}},
        ),
    ]
)
def test_command_sender_methods(
    command_sender: StreamDeckCommandSender,
    mock_client: Mock,
    method_name: str,
    context: str,
    extra_args: dict,
    expected_event: str,
    expected_payload: dict,
):
    """Parameterized test for StreamDeckCommandSender methods that send events."""
    # First, assert the command_sender object has the provided method name (i.e. "set_settings")
    assert hasattr(command_sender, method_name)

    method = getattr(command_sender, method_name)
    method(context, **extra_args)

    # Build the expected data structure to send through the WebSocket
    expected_data = {
        "context": context,
        "event": expected_event,
        **expected_payload,
    }

    # Assert that the client's send_event method was called with the expected data
    mock_client.send_event.assert_called_once_with(expected_data)