from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest
from streamdeck.event_listener import EventListener, EventListenerManager
from streamdeck.models.events import ApplicationDidLaunch, EventBase


if TYPE_CHECKING:
    from collections.abc import Generator
    from typing import Any, ClassVar

    from streamdeck.types import EventNameStr


class MockEventListener(EventListener):
    """Mock implementation of EventListener for testing."""
    event_models: ClassVar[list[type[EventBase]]] = [ApplicationDidLaunch]

    def __init__(self):
        self._running = True
        self.events = ["event1", "event2", "event3"]
        self.listen_called = False
        self.stop_called = False

    def listen(self) -> Generator[str, None, None]:
        self.listen_called = True
        for event in self.events:
            if not self._running:
                break
            yield event

    def stop(self) -> None:
        self._running = False
        self.stop_called = True


class SlowMockEventListener(EventListener):
    """Mock implementation of EventListener that yields events with a delay."""
    event_models: ClassVar[list[type[EventBase]]] = [ApplicationDidLaunch]

    def __init__(self, delay: float = 0.1):
        self._running = True
        self.delay = delay
        self.events = ["slow1", "slow2", "slow3"]

    def listen(self) -> Generator[str, None, None]:
        for event in self.events:
            if not self._running:
                break
            time.sleep(self.delay)  # simulate processing time
            yield event

    def stop(self) -> None:
        self._running = False


class ExceptionEventListener(EventListener):
    """Mock implementation of EventListener that raises an exception."""
    event_models: ClassVar[list[type[EventBase]]] = [ApplicationDidLaunch]

    def listen(self) -> Generator[str, None, None]:
        self._running = True
        # Raise exception after yielding one event
        yield "event_before_exception"
        raise ValueError("Test exception in listener")

    def stop(self) -> None:
        pass




def test_add_listener():
    """Test adding a listener to the manager."""
    manager = EventListenerManager()
    listener = Mock()

    assert len(manager.listeners_lookup_by_thread) == 0

    manager.add_listener(listener)

    # Check that a thread was created and added to the lookup dict
    assert len(manager.listeners_lookup_by_thread) == 1
    thread = next(iter(manager.listeners_lookup_by_thread.keys()))
    assert isinstance(thread, threading.Thread)
    assert manager.listeners_lookup_by_thread[thread] is listener


def test_event_stream_basic():
    """Test that event_stream yields events from added listeners."""
    manager = EventListenerManager()
    listener = MockEventListener()

    manager.add_listener(listener)

    # Collect the first few events
    events : list[EventNameStr] = []
    for event in manager.event_stream():
        events.append(event)  # type: ignore[arg-type]
        if len(events) >= 3:  # We expect 3 events from MockEventListener
            manager.stop()
            break

    # Check that we got the expected events
    assert events == listener.events


def test_event_stream_multiple_listeners():
    """Test that events from multiple listeners are interleaved."""
    manager = EventListenerManager()
    listener1 = MockEventListener()
    listener2 = SlowMockEventListener(delay=0.01)  # Small delay to ensure deterministic order

    manager.add_listener(listener1)
    manager.add_listener(listener2)

    # Collect all events
    events: list[EventNameStr] = []
    for event in manager.event_stream():
        events.append(event)  # type: ignore[arg-type]
        if len(events) >= 6:  # We expect 6 events total (3 from each listener)
            manager.stop()
            break

    # Check that we got all expected events (order may vary)
    assert len(events) == 6
    assert set(events) == {"event1", "event2", "event3", "slow1", "slow2", "slow3"}


def test_stop():
    """Test that stop() correctly stops all listeners."""
    manager = EventListenerManager()
    listener1 = MockEventListener()
    listener2 = MockEventListener()

    manager.add_listener(listener1)
    manager.add_listener(listener2)

    # Start the event stream but then immediately stop it
    event_iter = manager.event_stream()
    next(event_iter)  # Get the first event to ensure threads start
    manager.stop()

    # Check that all listeners were stopped
    assert listener1.stop_called
    assert listener2.stop_called
    assert not manager.running


@patch("streamdeck.event_listener.logger")
def test_listener_exception_handling(mock_logger: Mock):
    """Test that exceptions in listeners are properly caught and logged."""
    manager = EventListenerManager()
    listener = ExceptionEventListener()

    manager.add_listener(listener)

    # Collect events - should get one event before the exception
    events: list[Any] = []
    for event in manager.event_stream():
        events.append(event)
        if len(events) >= 1:  # We expect 1 event before exception
            time.sleep(0.1)  # Give time for exception to be raised
            manager.stop()
            break

    assert "event_before_exception" in events
    # Check that the exception was logged
    mock_logger.exception.assert_called_with("Unexpected error in wrapped listener %s. Stopping just this listener.", listener)


def test_listener_wrapper():
    """Test the _listener_wrapper method that runs listeners in threads."""
    manager = EventListenerManager()
    listener = MockEventListener()

    # Run the wrapper directly
    manager.running = True
    manager._listener_wrapper(listener)

    # Check that events were put in the queue
    assert manager.event_queue.qsize() == 3
    assert manager.event_queue.get() == "event1"
    assert manager.event_queue.get() == "event2"
    assert manager.event_queue.get() == "event3"
