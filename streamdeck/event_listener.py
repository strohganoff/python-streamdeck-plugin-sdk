from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from logging import getLogger
from queue import Queue
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Generator
    from typing import Any, ClassVar

    from typing_extensions import TypeIs

    from streamdeck.models.events import EventBase



logger = getLogger("streamdeck.event_listener")


class _SENTINAL:
    """A sentinel object used to signal the end of the event stream.

    Not meant to be instantiated, but rather used as a singleton (e.g. `_SENTINAL`).
    """
    @classmethod
    def is_sentinal(cls, event: str | bytes | type[_SENTINAL]) -> TypeIs[type[_SENTINAL]]:
        """Check if an event is the sentinal object. Provided to enable better type-checking."""
        return event is cls


class StopStreaming(Exception):  # noqa: N818
    """Raised by an EventListener implementation to signal that the entire EventManagerListener should stop streaming events."""


class EventListenerManager:
    """Manages event listeners and provides a shared event queue for them to push events into.

    With this class, a single event stream can be created from multiple listeners.
    This allows for us to listen for not only Stream Deck events, but also other events plugin-developer -defined events.
    """
    def __init__(self) -> None:
        self.event_queue: Queue[str | bytes | type[_SENTINAL]] = Queue()
        self.listeners_lookup_by_thread: dict[threading.Thread, EventListener] = {}
        self._running = False

    def add_listener(self, listener: EventListener) -> None:
        """Registers a listener function that yields events.

        Args:
            listener: A function that yields events.
        """
        # Create a thread for the listener
        thread = threading.Thread(
            target=self._listener_wrapper,
            args=(listener,),
            daemon=True,
        )
        self.listeners_lookup_by_thread[thread] = listener

    def _listener_wrapper(self, listener: EventListener) -> None:
        """Wraps the listener function: for each event yielded, push it into the shared queue."""
        try:
            for event in listener.listen():
                self.event_queue.put(event)

                if not self.running:
                    break

        except StopStreaming:
            logger.debug("Event listener requested to stop streaming.")
            self.event_queue.put(_SENTINAL)

        except Exception:
            logger.exception("Unexpected error in wrapped listener %s. Stopping just this listener.", listener)

    def stop(self) -> None:
        """Stops the event generation loop and waits for all threads to finish.

        Listeners will check the running flag if implemented to stop listening.
        """
        # Set the running flag to False to stop the listeners running in separate threads.
        self.running = False
        # Push the sentinel to immediately unblock the queue.get() in event_stream.
        self.event_queue.put(_SENTINAL)

        for thread in self.listeners_lookup_by_thread:
            logger.debug("Stopping listener %s.")
            self.listeners_lookup_by_thread[thread].stop()
            if thread.is_alive():
                thread.join()

            logger.info("All listeners have been stopped.")

    def event_stream(self) -> Generator[str | bytes, None, None]:
        """Starts all registered listeners, sets the running flag to True, and yields events from the shared queue."""
        logger.info("Starting event stream.")
        # Set the running flag to True and start the listeners in their separate threads.
        self.running = True
        for thread in self.listeners_lookup_by_thread:
            thread.start()

        try:
            while True:
                event = self.event_queue.get()
                if _SENTINAL.is_sentinal(event):
                    logger.debug("Sentinal received, stopping event stream.")
                    break  # Exit loop immediately if the sentinal is received
                yield event
        finally:
            self.stop()


class EventListener(ABC):
    """Base class for event listeners.

    Event listeners are classes that listen for events and simply yield them as they come.
    The EventListenerManager will handle the threading and pushing the events yielded into a shared queue.
    """
    event_models: ClassVar[list[type[EventBase]]]
    """A list of event models that the listener can yield. Read in by the PluginManager to model the incoming event data off of.

    The plugin-developer must define this list in their subclass.
    """

    @abstractmethod
    def listen(self) -> Generator[str | bytes, Any, None]:
        """Start listening for events and yield them as they come.

        This is the method that run in a separate thread.
        """

    @abstractmethod
    def stop(self) -> None:
        """Stop the listener. This could set an internal flag, close a connection, etc."""
