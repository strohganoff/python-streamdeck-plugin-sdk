from __future__ import annotations

from contextlib import nullcontext
from typing import TYPE_CHECKING, Annotated, Any, Union

import pytest
from pydantic import Discriminator, TypeAdapter
from streamdeck.models.events.base import EventBase


if TYPE_CHECKING:
    from _pytest.python_api import RaisesContext  # type: ignore[import]


class TestBaseSubscripting:
    """Test expected behavior of subscripting the base class."""
    common_test_parameters: pytest.MarkDecorator = pytest.mark.parametrize(
        ("subscript_value", "expected_context"),
        [
            ("ok", nullcontext()),
            (404, pytest.raises(TypeError)),
            (False, pytest.raises(TypeError)),
        ],
    )

    @common_test_parameters
    def test_base_type_subscripting(
        self,
        subscript_value: Any,
        expected_context: RaisesContext[TypeError] | nullcontext[None],
    ) -> None:
        """Test that only string types are allowed for base class subscripting."""
        with expected_context:
            EventBase[subscript_value]

    @common_test_parameters
    def test_base_type_subscription_subclassing(
        self,
        subscript_value: Any,
        expected_context: RaisesContext[TypeError] | nullcontext[None],
    ) -> None:
        """Test that only string types are allowed for base class subscripting--even in subclasses."""
        with expected_context:
            class MyEvent(EventBase[subscript_value]):  # type: ignore[valid-type]
                """Event model subclass with invalid event field type."""

    def test_subscripting_subclass_raises_type_error(self) -> None:
        """Test that subscripting the subclass raises a TypeError."""
        class MyEvent(EventBase["ok"]): ...
        with pytest.raises(TypeError):
            MyEvent["not_ok"]

        with pytest.raises(TypeError):
            class BadMyEventSubclass(MyEvent["also_not_ok"]): ...  # type: ignore[valid-type]

    def test_no_base_subscript_in_subclass_raises_type_error(self) -> None:
        """Test that subscripting the base class without a value raises a TypeError."""
        with pytest.raises(TypeError):
            class BadNoSubscriptEvent(EventBase):  # type: ignore[valid-type]
                ...

    # def test_overridden_event_name_raises_type_error(self) -> None:
    #     """Test that overriding the event name in a subclass raises a TypeError."""
    #     with pytest.raises(TypeError):
    #         class MyEvent(EventBase["ok"]):



def test_init_base_class_raises_error() -> None:
    """Test that initializing the base class directly raises a TypeError."""
    with pytest.raises(TypeError):
        EventBase(event="uhh")


def test_init_subscripted_subclass_raises_error() -> None:
    """Test that initializing a subscripted subclass of the base class raises a TypeError."""
    with pytest.raises(TypeError):
        EventBase["uhh"](event="uhh")



class TestBaseComparisons:
    """Test expected behavior of comparisons between EventBase and its subscripted subclasses."""
    def test_base_subtype_singleton_equality(self) -> None:
        concrete_base_subtype1 = EventBase["conc1"]

        assert concrete_base_subtype1 == EventBase["conc1"]
        assert concrete_base_subtype1 is EventBase["conc1"]


    def test_base_different_subtypes_inequality(self) -> None:
        concrete_base_subtype1 = EventBase["conc1"]
        concrete_base_subtype2 = EventBase["conc2"]

        assert concrete_base_subtype1 != concrete_base_subtype2


    def test_base_subtype_issubclass(self) -> None:
        concrete_base_subtype1 = EventBase["conc1"]

        class ConcreteEvent1(EventBase["conc1"]): ...

        assert issubclass(ConcreteEvent1, EventBase)
        assert issubclass(ConcreteEvent1, concrete_base_subtype1)


    def test_base_different_subtypes_not_issubclass(self) -> None:
        concrete_base_subtype1 = EventBase["conc1"]
        concrete_base_subtype2 = EventBase["conc2"]

        class ConcreteEvent1(EventBase["conc1"]): ...
        class ConcreteEvent2(EventBase["conc2"]): ...

        assert not issubclass(ConcreteEvent1, concrete_base_subtype2)
        assert not issubclass(ConcreteEvent2, concrete_base_subtype1)


    def test_subclass_isinstance_of_base_subtype(self) -> None:
        class ConcreteEvent1(EventBase["conc1"]): ...
        concrete_event_instance1 = ConcreteEvent1(event="conc1")

        assert isinstance(concrete_event_instance1, EventBase)
        assert isinstance(concrete_event_instance1, EventBase["conc1"])


    def test_subclass_not_isinstance_of_different_subtypes(self) -> None:
        concrete_base_subtype1 = EventBase["conc1"]
        concrete_base_subtype2 = EventBase["conc2"]

        class ConcreteEvent1(EventBase["conc1"]): ...
        class ConcreteEvent2(EventBase["conc2"]): ...

        concrete_event_instance1 = ConcreteEvent1(event="conc1")
        concrete_event_instance2 = ConcreteEvent2(event="conc2")

        assert not isinstance(concrete_event_instance1, ConcreteEvent2)
        assert not isinstance(concrete_event_instance1, concrete_base_subtype2)
        assert not isinstance(concrete_event_instance2, concrete_base_subtype1)


    def test_subclass_is_not_base_subtype(self) -> None:
        concrete_base_subtype1 = EventBase["conc1"]

        class ConcreteEvent1(EventBase["conc1"]): ...

        # ConcreteEvent1 is an instance of concrete_event_instance1, but not equal to nor "is" concrete_event_instance1 itself.
        assert ConcreteEvent1 != concrete_base_subtype1
        assert ConcreteEvent1 is not concrete_base_subtype1



def test_type_adapter() -> None:
    """Test that Event subclasses can be discriminated by the event field."""
    class ConcreteEvent(EventBase["concrete"]): ...
    class TestEvent(EventBase["test"]): ...
    class AnotherEvent(EventBase["another"]): ...
    class YetAnotherEvent(EventBase["yet_another"]): ...

    # Create a TypeAdapter for the base class
    adapter: TypeAdapter[EventBase] = TypeAdapter(
        Annotated[Union[ConcreteEvent, TestEvent, AnotherEvent, YetAnotherEvent], Discriminator("event")]  # noqa: UP007
    )

    concrete_event_instance = adapter.validate_json('{"event": "concrete"}')
    assert isinstance(concrete_event_instance, ConcreteEvent)

    test_event_instance = adapter.validate_json('{"event": "test"}')
    assert isinstance(test_event_instance, TestEvent)

    another_event_instance = adapter.validate_json('{"event": "another"}')
    assert isinstance(another_event_instance, AnotherEvent)

    yet_another_event_instance = adapter.validate_json('{"event": "yet_another"}')
    assert isinstance(yet_another_event_instance, YetAnotherEvent)
