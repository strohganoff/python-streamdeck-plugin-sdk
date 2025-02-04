from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import create_autospec

import pytest
from polyfactory.factories.pydantic_factory import ModelFactory
from streamdeck.actions import Action, ActionRegistry, GlobalAction
from streamdeck.models import events


if TYPE_CHECKING:
    from unittest.mock import Mock



@pytest.fixture
def mock_event_handler() -> Mock:
    def dummy_handler(event: events.EventBase) -> None:
        """Dummy event handler function that matches the EventHandlerFunc TypeAlias."""

    return create_autospec(dummy_handler, spec_set=True)


class ApplicationDidLaunchEventFactory(ModelFactory[events.ApplicationDidLaunchEvent]):
    """Polyfactory factory for creating fake applicationDidLaunch event message based on our Pydantic model.

    ApplicationDidLaunchEvent's hold no unique identifier properties, besides the almost irrelevant `event` name property.
    """

class DeviceDidConnectFactory(ModelFactory[events.DeviceDidConnectEvent]):
    """Polyfactory factory for creating fake deviceDidConnect event message based on our Pydantic model.

    DeviceDidConnectEvent's have `device` unique identifier property.
    """

class KeyDownEventFactory(ModelFactory[events.KeyDownEvent]):
    """Polyfactory factory for creating fake keyDown event message based on our Pydantic model.

    KeyDownEvent's have the unique identifier properties:
        `device`: Identifies the Stream Deck device that this event is associated with.
        `action`: Identifies the action that caused the event.
        `context`: Identifies the *instance* of an action that caused the event.
    """


@pytest.mark.parametrize(("event_name","event_factory"), [
    ("keyDown", KeyDownEventFactory),
    ("deviceDidConnect", DeviceDidConnectFactory),
    ("applicationDidLaunch", ApplicationDidLaunchEventFactory)
])
def test_global_action_gets_triggered_by_event(
    mock_event_handler: Mock,
    event_name: str,
    event_factory: ModelFactory[events.EventBase],
):
    """Test that a global action's event handlers are triggered by an event.

    Global actions should be triggered by any event type that is registered with them,
      regardless of the event's unique identifier properties (or whether they're even present).
    """
    fake_event_data = event_factory.build()

    global_action = GlobalAction()

    global_action.on(event_name)(mock_event_handler)

    for handler in global_action.get_event_handlers(event_name):
        handler(fake_event_data)

    assert mock_event_handler.call_count == 1
    assert fake_event_data in mock_event_handler.call_args.args


@pytest.mark.parametrize(("event_name","event_factory"), [
    ("keyDown", KeyDownEventFactory),
    ("deviceDidConnect", DeviceDidConnectFactory),
    ("applicationDidLaunch", ApplicationDidLaunchEventFactory)
])
def test_action_gets_triggered_by_event(mock_event_handler: Mock, event_name: str, event_factory: ModelFactory[events.EventBase]):
    # Create a fake event model instance
    fake_event_data: events.EventBase = event_factory.build()
    # Extract the action UUID from the fake event data, or use a default value
    action_uuid: str = fake_event_data.action if fake_event_data.is_action_specific() else "my-fake-action-uuid"

    action = Action(uuid=action_uuid)

    # Register the mock event handler with the action
    action.on(event_name)(mock_event_handler)

    # Get the action's event handlers for the event and call them
    for handler in action.get_event_handlers(event_name):
        handler(fake_event_data)

    # For some reason, assert_called_once() and assert_called_once_with() are returning False here...
    # assert mock_event_handler.assert_called_once(fake_event_data)
    assert mock_event_handler.call_count == 1
    assert fake_event_data in mock_event_handler.call_args.args



@pytest.mark.parametrize(("event_name","event_factory"), [
    ("keyDown", KeyDownEventFactory),
    ("deviceDidConnect", DeviceDidConnectFactory),
    ("applicationDidLaunch", ApplicationDidLaunchEventFactory)
])
def test_global_action_registry_get_action_handlers_filtering(mock_event_handler: Mock, event_name: str, event_factory: ModelFactory[events.EventBase]):
    # Create a fake event model instance
    fake_event_data: events.EventBase = event_factory.build()
    # Extract the action UUID from the fake event data, or use a default value
    action_uuid: str = fake_event_data.action if fake_event_data.is_action_specific() else None

    registry = ActionRegistry()
    # Create an Action instance, without an action UUID as global actions aren't associated with a specific action
    global_action = GlobalAction()

    global_action.on(event_name)(mock_event_handler)

    # Register the global action with the registry
    registry.register(global_action)

    for handler in registry.get_action_handlers(
        event_name=fake_event_data.event,
        event_action_uuid=action_uuid,
    ):
        handler(fake_event_data)

    assert mock_event_handler.call_count == 1
    assert fake_event_data in mock_event_handler.call_args.args



@pytest.mark.parametrize(("event_name","event_factory"), [
    ("keyDown", KeyDownEventFactory),
    ("deviceDidConnect", DeviceDidConnectFactory),
    ("applicationDidLaunch", ApplicationDidLaunchEventFactory)
])
def test_action_registry_get_action_handlers_filtering(mock_event_handler: Mock, event_name: str, event_factory: ModelFactory[events.EventBase]):
    # Create a fake event model instance
    fake_event_data: events.EventBase = event_factory.build()
    # Extract the action UUID from the fake event data, or use a default value
    action_uuid: str = fake_event_data.action if fake_event_data.is_action_specific() else None

    registry = ActionRegistry()
    # Create an Action instance, using either the fake event's action UUID or a default value
    action = Action(uuid=action_uuid or "my-fake-action-uuid")

    action.on(event_name)(mock_event_handler)

    # Register the action with the registry
    registry.register(action)

    for handler in registry.get_action_handlers(
        event_name=fake_event_data.event,
        event_action_uuid=action_uuid,  # This will be None if the event is not action-specific (i.e. doesn't have an action UUID property)
    ):
        handler(fake_event_data)

    assert mock_event_handler.call_count == 1
    assert fake_event_data in mock_event_handler.call_args.args



def test_multiple_actions_filtering():
    registry = ActionRegistry()
    action = Action("my-fake-action-uuid-1")
    global_action = GlobalAction()

    global_action_event_handler_called = False
    action_event_handler_called = False

    @global_action.on("applicationDidLaunch")
    def _global_app_did_launch_action_handler(event: events.EventBase):
        nonlocal global_action_event_handler_called
        global_action_event_handler_called = True

    @action.on("keyDown")
    def _action_key_down_event_handler(event: events.EventBase):
        nonlocal action_event_handler_called
        action_event_handler_called = True

    # Register both actions with the registry
    registry.register(global_action)
    registry.register(action)

    # Create a fake event model instances
    fake_app_did_launch_event_data: events.ApplicationDidLaunchEvent = ApplicationDidLaunchEventFactory.build()
    fake_key_down_event_data: events.KeyDownEvent = KeyDownEventFactory.build(action=action.uuid)

    for handler in registry.get_action_handlers(event_name=fake_app_did_launch_event_data.event):
        handler(fake_app_did_launch_event_data)

    assert global_action_event_handler_called
    assert not action_event_handler_called

    # Reset the flag for global action event handler
    global_action_event_handler_called = False

    # Get the action handlers for the event and call them
    for handler in registry.get_action_handlers(event_name=fake_key_down_event_data.event, event_action_uuid=fake_key_down_event_data.action):
        handler(fake_key_down_event_data)

    assert action_event_handler_called
    assert not global_action_event_handler_called
