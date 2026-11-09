"""Tests for the generic incoming event base model."""

from __future__ import annotations

from typing import Any, Literal

import pytest
from pydantic import TypeAdapter, ValidationError

from streamdeck.models.events.base import EventBase


@pytest.mark.parametrize(
    "event_name_type",
    [str, Literal[404], Literal[False], Literal["ok", 404]],
)
def test_event_name_type_must_be_literal_of_strings(event_name_type: Any) -> None:  # noqa: ANN401
    """Only Literal types containing strings can specialize EventBase."""
    with pytest.raises(TypeError):
        EventBase[event_name_type]


def test_event_base_must_be_specialized_when_subclassed() -> None:
    """Concrete event models must specialize EventBase with a Literal."""
    with pytest.raises(TypeError, match="specialized EventBase"):

        class BadEvent(EventBase): ...


def test_string_literal_specialization_records_event_names() -> None:
    """A concrete event subclass inherits the names from its Literal specialization."""

    class MyEvent(EventBase[Literal["ok"]]): ...

    assert MyEvent.get_model_event_names() == ("ok",)
    assert MyEvent.__event_type__() == Literal["ok"]


def test_multiple_string_literal_values_are_supported() -> None:
    """A single event model may declare more than one accepted event name."""

    class MyEvent(EventBase[Literal["ok", "also_ok"]]): ...

    assert MyEvent.get_model_event_names() == ("ok", "also_ok")
    assert TypeAdapter(MyEvent).validate_python({"event": "ok"}) == MyEvent(event="ok")
    assert TypeAdapter(MyEvent).validate_python({"event": "also_ok"}) == MyEvent(event="also_ok")
    with pytest.raises(ValidationError):
        TypeAdapter(MyEvent).validate_python({"event": "bad"})


def test_event_base_and_generic_specialization_cannot_be_instantiated() -> None:
    """Only concrete event model subclasses can be instantiated."""
    with pytest.raises(TypeError, match="directly"):
        EventBase(event="uhh")

    with pytest.raises(TypeError, match="directly"):
        EventBase[Literal["uhh"]](event="uhh")


def test_generic_specializations_are_cached() -> None:
    """Pydantic returns the same specialized class for repeated type arguments."""
    specialized_base = EventBase[Literal["conc1"]]

    assert specialized_base is EventBase[Literal["conc1"]]
    assert specialized_base != EventBase[Literal["conc2"]]


def test_concrete_subclass_is_a_subclass_of_its_specialized_base() -> None:
    """Concrete event models inherit the specialized Pydantic model class."""
    specialized_base = EventBase[Literal["conc1"]]

    class ConcreteEvent(specialized_base): ...

    event = ConcreteEvent(event="conc1")
    assert issubclass(ConcreteEvent, EventBase)
    assert issubclass(ConcreteEvent, specialized_base)
    assert isinstance(event, EventBase)
    assert isinstance(event, specialized_base)


def test_subclasses_of_event_models_keep_event_metadata() -> None:
    """Further subclasses retain the event name metadata of their base model."""

    class ConcreteEvent(EventBase[Literal["conc1"]]): ...

    class ChildEvent(ConcreteEvent): ...

    assert ChildEvent.get_model_event_names() == ("conc1",)
