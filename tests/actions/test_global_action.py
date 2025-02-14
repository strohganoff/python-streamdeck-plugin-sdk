from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from streamdeck.actions import GlobalAction, available_event_names


if TYPE_CHECKING:
    from streamdeck.models.events import EventBase


def test_global_action_register_event_handler():
    """Test that an event handler can be registered for each valid event name."""
    global_action = GlobalAction()

    for event_name in available_event_names:
        @global_action.on(event_name)
        def handler(event: EventBase) -> None:
            pass

        # Ensure the handler is registered for the correct event name
        assert len(global_action._events[event_name]) == 1
        assert handler in global_action._events[event_name]


def test_global_action_register_invalid_event_handler():
    """Test that attempting to register an invalid event handler raises an exception."""
    global_action = GlobalAction()

    with pytest.raises(Exception):
        @global_action.on("InvalidEvent")
        def handler(event: EventBase):
            pass


def test_global_action_get_event_handlers():
    """Test that the correct event handlers are retrieved for each event name."""
    global_action = GlobalAction()

    for event_name in available_event_names:
        # Register a handler for the event name
        @global_action.on(event_name)
        def handler(event: EventBase):
            pass

        # Retrieve the handlers using the generator
        handlers = list(global_action.get_event_handlers(event_name))

        # Ensure that the correct handler is retrieved
        assert len(handlers) == 1
        assert handlers[0] == handler


def test_global_action_get_event_handlers_no_event_registered():
    """Test that attempting to get handlers for an event with no registered handlers raises an exception."""
    global_action = GlobalAction()

    with pytest.raises(Exception):
        list(global_action.get_event_handlers("InvalidEvent"))


def test_global_action_register_multiple_handlers_for_event():
    """Test that multiple handlers can be registered for an event."""
    global_action = GlobalAction()

    @global_action.on("keyDown")
    def handler_one(event: EventBase):
        pass

    @global_action.on("keyDown")
    def handler_two(event: EventBase):
        pass

    handlers = list(global_action.get_event_handlers("keyDown"))

    # Ensure both handlers are registered for the event
    assert len(handlers) == 2
    assert handler_one in handlers
    assert handler_two in handlers


def test_global_action_get_event_handlers_invalid_event():
    """Test that attempting to get handlers for an invalid event raises a KeyError."""
    global_action = GlobalAction()

    with pytest.raises(KeyError):
        list(global_action.get_event_handlers("InvalidEvent"))
