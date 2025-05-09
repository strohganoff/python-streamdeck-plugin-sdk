from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from streamdeck.event_handlers.handler_methods import HandlerMethodCatalogMixin, on
from streamdeck.event_handlers.registry import HandlersRegistry


if TYPE_CHECKING:
    from streamdeck.models.events import EventBase



def test_dispatch_from_registry() -> None:
    """Test that the HandlersRegistry.get_event_handlers method works as expected on a HandlerMethodCatalogMixin implementation."""

    class TestCatalogClass(HandlerMethodCatalogMixin):
        def __init__(self) -> None:
            self.handler_called =  False

        @on("test_event")
        def test_event_handler(self, event_data: EventBase) -> None:
            self.handler_called = True

    test_catalog = TestCatalogClass()

    registry = HandlersRegistry()
    registry.register(test_catalog)

    handlers = list(registry.get_event_handlers("test_event"))

    assert len(handlers) == 1
    assert handlers[0] == test_catalog.test_event_handler

    handlers[0]({"key": "value"})

    assert test_catalog.handler_called


def test_get_registered_event_names() -> None:
    """Test that the get_registered_event_names method works as expected, and that it doesn't include handlers from other HandlerMethodCatalogMixin subclasses."""
    class TestCatalogClass(HandlerMethodCatalogMixin):
        @on("testEvent1")
        def test_event_handler(self, event_data: dict[str, str]) -> None:
            pass

        @on("testEvent2")
        def another_event_handler(self, event_data: dict[str, str]) -> None:
            pass

    class IgnoredCatalogClass(HandlerMethodCatalogMixin):
        """Since each subclass should have its own list of registered handlers, this class' handlers should not be included in TestCatalogClass's list."""
        @on("ignoreThisEventName")
        def ignore_this_event_handler(self, event_data: dict[str, str]) -> None:
            pass

    test_catalog = TestCatalogClass()

    event_names = test_catalog.get_registered_event_names()
    assert len(event_names) == 2
    assert event_names == ["testEvent1", "testEvent2"]
