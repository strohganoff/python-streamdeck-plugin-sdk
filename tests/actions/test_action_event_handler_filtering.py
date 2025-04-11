from __future__ import annotations

from typing import TYPE_CHECKING, cast
from unittest.mock import create_autospec

import pytest
from streamdeck.actions import Action, ActionRegistry, GlobalAction
from streamdeck.models.events.common import ContextualEventMixin

from tests.test_utils.fake_event_factories import (
    ApplicationDidLaunchEventFactory,
    DeviceDidConnectFactory,
    KeyDownEventFactory,
)


if TYPE_CHECKING:
    from unittest.mock import Mock

    from polyfactory.factories.pydantic_factory import ModelFactory
    from streamdeck.models import events
    from streamdeck.models.events.base import LiteralStrGenericAlias



@pytest.fixture
def mock_event_handler() -> Mock:
    def dummy_handler(event: events.EventBase) -> None:
        """Dummy event handler function that matches the EventHandlerFunc TypeAlias."""

    return create_autospec(dummy_handler, spec_set=True)


@pytest.fixture(params=[
    KeyDownEventFactory,
    DeviceDidConnectFactory,
    ApplicationDidLaunchEventFactory
])
def fake_event_data(request: pytest.FixtureRequest) -> events.EventBase[LiteralStrGenericAlias]:
    event_factory = cast("ModelFactory[events.EventBase[LiteralStrGenericAlias]]", request.param)
    return event_factory.build()


def test_global_action_gets_triggered_by_event(
    mock_event_handler: Mock,
    fake_event_data: events.EventBase[LiteralStrGenericAlias],
) -> None:
    """Test that a global action's event handlers are triggered by an event.

    Global actions should be triggered by any event type that is registered with them,
      regardless of the event's unique identifier properties (or whether they're even present).
    """
    global_action = GlobalAction()

    global_action.on(fake_event_data.event)(mock_event_handler)

    for handler in global_action.get_event_handlers(fake_event_data.event):
        handler(fake_event_data)

    assert mock_event_handler.call_count == 1
    assert fake_event_data in mock_event_handler.call_args.args


def test_action_gets_triggered_by_event(
    mock_event_handler: Mock,
    fake_event_data: events.EventBase[LiteralStrGenericAlias],
) -> None:
    """Test that an action's event handlers are triggered by an event.

    Actions should only be triggered by events that have the same unique identifier properties as the action.
    """
    # Extract the action UUID from the fake event data, or use a default value
    action_uuid: str = fake_event_data.action if isinstance(fake_event_data, ContextualEventMixin) else "my-fake-action-uuid"

    action = Action(uuid=action_uuid)

    # Register the mock event handler with the action
    action.on(fake_event_data.event)(mock_event_handler)

    # Get the action's event handlers for the event and call them
    for handler in action.get_event_handlers(fake_event_data.event):
        handler(fake_event_data)

    # For some reason, assert_called_once() and assert_called_once_with() are returning False here...
    # assert mock_event_handler.assert_called_once(fake_event_data)
    assert mock_event_handler.call_count == 1
    assert fake_event_data in mock_event_handler.call_args.args



def test_global_action_registry_get_action_handlers_filtering(
    mock_event_handler: Mock,
    fake_event_data: events.EventBase[LiteralStrGenericAlias],
) -> None:
    # Extract the action UUID from the fake event data, or use a default value
    action_uuid: str | None = fake_event_data.action if isinstance(fake_event_data, ContextualEventMixin) else None

    registry = ActionRegistry()
    # Create an Action instance, without an action UUID as global actions aren't associated with a specific action
    global_action = GlobalAction()

    global_action.on(fake_event_data.event)(mock_event_handler)

    # Register the global action with the registry
    registry.register(global_action)

    for handler in registry.get_action_handlers(
        event_name=fake_event_data.event,
        event_action_uuid=action_uuid,
    ):
        handler(fake_event_data)

    assert mock_event_handler.call_count == 1
    assert fake_event_data in mock_event_handler.call_args.args



def test_action_registry_get_action_handlers_filtering(
    mock_event_handler: Mock,
    fake_event_data: events.EventBase[LiteralStrGenericAlias],
) -> None:
    # Extract the action UUID from the fake event data, or use a default value
    action_uuid: str | None = fake_event_data.action if isinstance(fake_event_data, ContextualEventMixin) else None

    registry = ActionRegistry()
    # Create an Action instance, using either the fake event's action UUID or a default value
    action = Action(uuid=action_uuid or "my-fake-action-uuid")

    action.on(fake_event_data.event)(mock_event_handler)

    # Register the action with the registry
    registry.register(action)

    for handler in registry.get_action_handlers(
        event_name=fake_event_data.event,
        event_action_uuid=action_uuid,  # This will be None if the event is not action-specific (i.e. doesn't have an action UUID property)
    ):
        handler(fake_event_data)

    assert mock_event_handler.call_count == 1
    assert fake_event_data in mock_event_handler.call_args.args



def test_multiple_actions_filtering() -> None:
    registry = ActionRegistry()
    action = Action("my-fake-action-uuid-1")
    global_action = GlobalAction()

    global_action_event_handler_called = False
    action_event_handler_called = False

    @global_action.on("applicationDidLaunch")
    def _global_app_did_launch_action_handler(event: events.EventBase[LiteralStrGenericAlias]) -> None:
        nonlocal global_action_event_handler_called
        global_action_event_handler_called = True

    @action.on("keyDown")
    def _action_key_down_event_handler(event: events.EventBase[LiteralStrGenericAlias]) -> None:
        nonlocal action_event_handler_called
        action_event_handler_called = True

    # Register both actions with the registry
    registry.register(global_action)
    registry.register(action)

    # Create a fake event model instances
    fake_app_did_launch_event_data: events.ApplicationDidLaunch = ApplicationDidLaunchEventFactory.build()
    fake_key_down_event_data: events.KeyDown = KeyDownEventFactory.build(action=action.uuid)

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
