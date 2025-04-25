from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from streamdeck.actions import Action, ActionRegistry

from tests.test_utils.fake_event_factories import (
    DialDownEventFactory,
    DialUpEventFactory,
    KeyUpEventFactory,
)


if TYPE_CHECKING:
    from streamdeck.models import events


def test_register_action() -> None:
    """Test that an action can be registered."""
    registry = ActionRegistry()
    action = Action("my-fake-action-uuid")

    assert len(registry._plugin_actions) == 0

    registry.register(action)
    assert len(registry._plugin_actions) == 1
    assert registry._plugin_actions[0] == action


def test_get_action_handlers_no_handlers() -> None:
    """Test that getting action handlers when there are no handlers yields nothing."""
    registry = ActionRegistry()
    action = Action("my-fake-action-uuid")

    registry.register(action)

    fake_event_data: events.DialUp = DialUpEventFactory.build()
    handlers = list(registry.get_action_handlers(event_name=fake_event_data.event, event_action_uuid=fake_event_data.action))
    assert len(handlers) == 0


def test_get_action_handlers_with_handlers() -> None:
    """Test that registered event handlers can be retrieved correctly."""
    registry = ActionRegistry()
    action = Action("my-fake-action-uuid")

    @action.on("dialDown")
    def dial_down_handler(event_data: events.EventBase) -> None:
        pass

    registry.register(action)

    fake_event_data: events.DialDown = DialDownEventFactory.build(action=action.uuid)
    handlers = list(registry.get_action_handlers(event_name=fake_event_data.event, event_action_uuid=fake_event_data.action))
    # handlers = list(registry.get_action_handlers("dialDown"))
    assert len(handlers) == 1
    assert handlers[0] == dial_down_handler


def test_get_action_handlers_multiple_actions() -> None:
    """Test that multiple actions with registered handlers return all handlers."""
    registry = ActionRegistry()

    action1 = Action("fake-action-uuid-1")
    action2 = Action("fake-action-uuid-2")

    @action1.on("keyUp")
    def key_up_handler1(event_data: events.EventBase) -> None:
        pass

    @action2.on("keyUp")
    def key_up_handler2(event_data: events.EventBase) -> None:
        pass

    registry.register(action1)
    registry.register(action2)

    fake_event_data: events.KeyUp = KeyUpEventFactory.build(action=action1.uuid)
    # Notice no action uuid is passed in here, so we should get all handlers for the event.
    handlers = list(registry.get_action_handlers(event_name=fake_event_data.event))

    assert len(handlers) == 2
    assert key_up_handler1 in handlers
    assert key_up_handler2 in handlers
