from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from streamdeck.actions import Action, available_event_names


if TYPE_CHECKING:
    from streamdeck.models.events import EventBase
    from streamdeck.types import EventNameStr


@pytest.mark.parametrize("event_name", list(available_event_names))
def test_action_register_event_handler(event_name: EventNameStr):
    """Test that an event handler can be registered for each valid event name."""
    action = Action("test.uuid.for.action")

    @action.on(event_name)
    def handler(event: EventBase) -> None:
        pass

    # Ensure the handler is registered for the correct event name
    assert len(action._events[event_name]) == 1
    assert handler in action._events[event_name]


def test_action_register_invalid_event_handler():
    """Test that attempting to register an invalid event handler raises an exception."""
    action = Action("test.uuid.for.action")

    with pytest.raises(Exception):
        @action.on("InvalidEvent")
        def handler(event: EventBase):
            pass


@pytest.mark.parametrize("event_name", list(available_event_names))
def test_action_get_event_handlers(event_name: EventNameStr):
    """Test that the correct event handlers are retrieved for each event name."""
    action = Action("test.uuid.for.action")

    # Register a handler for the event name
    @action.on(event_name)
    def handler(event: EventBase):
        pass

    # Retrieve the handlers using the generator
    handlers = list(action.get_event_handlers(event_name))

    # Ensure that the correct handler is retrieved
    assert len(handlers) == 1
    assert handlers[0] == handler


def test_action_get_event_handlers_no_event_registered():
    """Test that attempting to get handlers for an event with no registered handlers raises an exception."""
    action = Action("test.uuid.for.action")

    with pytest.raises(Exception):
        list(action.get_event_handlers("InvalidEvent"))  # type: ignore


def test_action_register_multiple_handlers_for_event():
    """Test that multiple handlers can be registered for the same event on the same action."""
    action = Action("test.uuid.for.action")

    @action.on("keyDown")
    def handler_one(event: EventBase):
        pass

    @action.on("keyDown")
    def handler_two(event: EventBase):
        pass

    handlers = list(action.get_event_handlers("keyDown"))

    # Ensure both handlers are retrieved
    assert len(handlers) == 2
    assert handler_one in handlers
    assert handler_two in handlers

def test_action_get_event_handlers_invalid_event():
    """Test that getting handlers for an invalid event raises a KeyError."""
    action = Action("test.uuid.for.action")

    with pytest.raises(KeyError):
        list(action.get_event_handlers("invalidEvent"))