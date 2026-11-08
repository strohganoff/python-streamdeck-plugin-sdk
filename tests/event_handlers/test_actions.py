from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import pytest
from streamdeck.event_handlers.actions import Action, ActionBase, GlobalAction
from streamdeck.models.events import DEFAULT_EVENT_NAMES


if TYPE_CHECKING:
    from streamdeck.models.events import EventBase


@pytest.fixture(params=[[Action, ("test.uuid.for.action",)], [GlobalAction, ()]])
def action(request: pytest.FixtureRequest) -> ActionBase:
    """Fixture for initializing the Action and GlobalAction classes to parameterize the tests.

    We have to initialize the classes here to ensure fresh instances are used to avoid sharing data between tests.
    """
    action_class, init_args = cast("tuple[type[ActionBase], tuple[Any]]", request.param)
    return action_class(*init_args)


@pytest.mark.parametrize("event_name", list(DEFAULT_EVENT_NAMES))
def test_action_register_event_handler(action: ActionBase, event_name: str) -> None:
    """Test that an event handler can be registered for each valid event name."""
    @action.on(event_name)
    def handler(event_data: EventBase) -> None:
        pass

    # Ensure the handler is registered for the correct event name
    assert len(action._events[event_name]) == 1
    assert handler in action._events[event_name]


@pytest.mark.parametrize(
    "handler",
    [
        lambda: None,
        lambda not_event_data: None,
        lambda *, event_data: None,
        lambda event_data=None: None,
    ],
)
def test_action_rejects_invalid_handler_signature(action: ActionBase, handler: Any) -> None:
    """Reject handlers that do not start with a required positional event parameter."""
    with pytest.raises(TypeError, match="Invalid event handler signature"):
        action.on("keyDown")(handler)


def test_action_accepts_optional_handler_parameters(action: ActionBase) -> None:
    """Optional trailing parameters don't prevent dispatch from calling a handler."""
    def handler(event_data: EventBase, unused: object | None = None) -> None:
        pass

    action.on("keyDown")(handler)

    assert handler in action._events["keyDown"]


def test_action_accepts_keyword_only_command_sender(action: ActionBase) -> None:
    """The command sender can be injected into a keyword-only parameter."""
    def handler(event_data: EventBase, *, command_sender: object) -> None:
        pass

    action.on("keyDown")(handler)

    assert handler in action._events["keyDown"]


def test_action_get_event_handlers(action: ActionBase) -> None:
    """Test that the correct event handlers are retrieved for each event name."""
    # Each iteration will add to the action's event handlers, thus we're checking that
    # even with multiple event names, the handlers are correctly retrieved.
    for _, event_name in enumerate(DEFAULT_EVENT_NAMES):
        # Register a handler for the given event name
        @action.on(event_name)
        def handler(event_data: EventBase) -> None:
            pass

        # Retrieve the handlers using the generator
        handlers = list(action.get_event_handlers(event_name))

        # Ensure that the correct handler is retrieved
        assert len(handlers) == 1
        assert handlers[0] == handler


def test_action_get_event_handlers_no_event_registered(action: ActionBase) -> None:
    """Test that attempting to get handlers for an event with no registered handlers returns an empty list.

    An implicit assumption is that an exception is not raised.
    """
    handlers = list(action.get_event_handlers("dialDown"))
    assert len(handlers) == 0


def test_action_get_event_handlers_invalid_event_name(action: ActionBase) -> None:
    """Test that attempting to get handlers for an event with an invalid event name returns an empty list.

    An implicit assumption is that an exception is not raised.
    """
    events = list(action.get_event_handlers("invalidEvent"))
    assert len(events) == 0


@pytest.mark.parametrize("action", [Action("test.uuid.for.action"), GlobalAction()])
def test_action_register_multiple_handlers_for_event(action: ActionBase) -> None:
    """Test that multiple handlers can be registered for the same event on the same action."""
    @action.on("keyDown")
    def handler_one(event_data: EventBase) -> None:
        pass

    @action.on("keyDown")
    def handler_two(event_data: EventBase) -> None:
        pass

    handlers = list(action.get_event_handlers("keyDown"))

    # Ensure both handlers are retrieved
    assert len(handlers) == 2
    assert handler_one in handlers
    assert handler_two in handlers
