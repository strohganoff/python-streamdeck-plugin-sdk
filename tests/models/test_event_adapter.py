import json
from typing import Literal

import pytest
from pydantic import ValidationError
from streamdeck.models.events import DEFAULT_EVENT_MODELS, DEFAULT_EVENT_NAMES, EventBase, KeyDown
from streamdeck.models.events.adapter import (
    EventAdapter,
)

from tests.test_utils.fake_event_factories import KeyDownEventFactory


def test_init_with_default_models() -> None:
    """Test that the EventAdapter initializes with just the default models and their event names."""
    adapter = EventAdapter()

    # Check that all default event names are registered
    assert len(adapter._event_names) == len(DEFAULT_EVENT_NAMES)
    for event_name in DEFAULT_EVENT_NAMES:
        assert event_name in adapter._event_names

    # Check that all default models are registered
    assert len(adapter._models) == len(DEFAULT_EVENT_MODELS)
    for model in DEFAULT_EVENT_MODELS:
        assert model in adapter._models

def test_add_model() -> None:
    """Test that models can be added to the adapter."""
    adapter = EventAdapter()

    # Create a fake event model
    class DummyEvent(EventBase["dummyEvent"]):
        payload: dict[str, str]

    # Add the custom model
    adapter.add_model(DummyEvent)

    # Check that the custom event name is registered
    assert "dummyEvent" in adapter._event_names
    assert len(adapter._event_names) == len(DEFAULT_EVENT_NAMES) + 1

    # Check that the custom model is registered
    assert DummyEvent in adapter._models
    assert len(adapter._models) == len(DEFAULT_EVENT_MODELS) + 1

def test_event_name_exists() -> None:
    """Test that event_name_exists correctly identifies registered events."""
    adapter = EventAdapter()

    # Should return True for default events
    assert adapter.event_name_exists("keyDown")
    assert adapter.event_name_exists("willAppear")

    # Should return False for non-registered events
    assert not adapter.event_name_exists("nonExistentEvent")

def test_type_adapter_creation() -> None:
    """Test that the type_adapter property creates a TypeAdapter."""
    adapter = EventAdapter()

    # First access should create the type adapter
    type_adapter = adapter.type_adapter
    assert type_adapter is not None

    # Second access should return the same instance
    assert adapter.type_adapter is type_adapter

def test_validate_json_with_valid_data() -> None:
    """Test that validate_json correctly parses valid JSON into the correct event model instance."""
    adapter = EventAdapter()

    # Create valid JSON for a keyDown event
    fake_key_down_event: KeyDown = KeyDownEventFactory.build()
    fake_key_down_json: str = fake_key_down_event.model_dump_json()

    # "Adapt" the JSON to an event model instance
    event = adapter.validate_json(fake_key_down_json)

    # Check that the event is parsed correctly
    assert isinstance(event, KeyDown)
    assert event == fake_key_down_event

@pytest.mark.parametrize("invalid_event_json", [
    json.dumps({"event": "keyDown"}),  # Missing required fields: action, context, device
    json.dumps({"event": "unknownEvent", "action": "com.example.plugin.action", "context": "context123"}) # Unknown event
])
def test_validate_json_with_invalid_data(invalid_event_json: str) -> None:
    """Test that validate_json raises an error for invalid JSON.

    Parameter 1: json object that is missing required fields.
    Parameter 2: json object with an unknown event name.
    """
    adapter = EventAdapter()

    # Validate the JSON - should raise ValidationError
    with pytest.raises(ValidationError):
        adapter.validate_json(invalid_event_json)


def test_adding_custom_event_allows_validation() -> None:
    """Test that adding a custom event allows validating JSON for that event."""
    adapter = EventAdapter()

    # Create a fake event model
    class DummyEvent(EventBase["dummyEvent"]):
        action: str
        context: str
        device: str
        payload: dict[str, str]

    # Add the custom model
    adapter.add_model(DummyEvent)

    # Create valid JSON for the custom event
    fake_event = DummyEvent(
        event="dummyEvent",
        action="com.example.plugin.action",
        context="context123",
        device="device123",
        payload={"key": "value"}
    )
    fake_event_json = fake_event.model_dump_json()

    # Validate the JSON
    event = adapter.validate_json(fake_event_json)

    # Check that the event is parsed correctly
    assert isinstance(event, DummyEvent)
    assert event == fake_event
