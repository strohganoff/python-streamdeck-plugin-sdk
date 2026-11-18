"""Run asynchronous event listeners and merge their output into one stream.

`EventListener` defines the interface for custom asynchronous event sources.
`EventListenerManager` runs registered listeners concurrently and forwards
their JSON messages through a shared stream, where the plugin runtime can
validate and dispatch them alongside built-in events. Listener event models
are registered separately by `PluginManager`.

A listener may raise `StopStreaming` to request shutdown of the merged stream.
Normal completion or an unexpected failure only ends that listener; the
manager keeps the stream open until a listener requests stream-wide shutdown
or the consumer cancels or closes the stream. During cleanup, the manager
stops each listener and cancels and awaits its associated task.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from logging import getLogger
from typing import TYPE_CHECKING

from exceptiongroup import ExceptionGroup
from typing_extensions import sentinel


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Awaitable
    from typing import ClassVar

    from streamdeck.models.events import EventBase


logger = getLogger("streamdeck.event_listener")

_END_OF_STREAM = sentinel("_END_OF_STREAM")
"""Private queue marker requesting termination of the merged event stream."""


class StopStreaming(Exception):  # noqa: N818
    """Signal that the complete merged event stream should stop.

    A listener can raise this exception when its source determines that the
    plugin runtime should shut down. The listener manager treats it as a
    stream-wide control signal rather than logging it as an unexpected
    listener failure.
    """


@dataclass
class _ListenerRegistration:
    """Keep one listener together with the task that runs it, if started."""

    listener: EventListener
    task: asyncio.Task[None] | None = None

    async def cleanup(self) -> list[BaseException]:
        """Stop this listener and await its task, collecting either failure."""
        operations: list[Awaitable[None]] = [self.listener.stop()]
        task = self.task

        # If this registration has a task, then ensure that it gets stopped
        if task is not None:
            if not task.done():
                task.cancel()
            operations.append(task)

        results = await asyncio.gather(*operations, return_exceptions=True)
        errors: list[BaseException] = []

        # The first result is the listener's stop result.
        listener_stop_result = results[0]
        if isinstance(listener_stop_result, BaseException):
            errors.append(listener_stop_result)

        # When this registration has a task, the second result is its outcome.
        if task is not None:
            task_result = results[1]
            if isinstance(task_result, BaseException) and not isinstance(
                task_result, asyncio.CancelledError
            ):
                errors.append(task_result)

        return errors


class EventListenerManager:
    """Coordinate event listeners and expose their output as one async stream.

    The manager starts each registered listener in its own asyncio task and
    forwards yielded messages through a shared async queue. Consumers receive
    messages from all listeners through :meth:`event_stream`, without needing
    to know which listener produced each message. The manager also handles
    listener failures, stream-wide stop requests, cancellation, and listener
    cleanup.
    """

    def __init__(self) -> None:
        self._listeners: list[_ListenerRegistration] = []
        self._event_queue: asyncio.Queue[str | bytes | _END_OF_STREAM] = asyncio.Queue()
        self._cleanup_started = False

    def add_listener(self, listener: EventListener) -> None:
        """Register a listener to be started with the next event stream.

        Listeners must be registered before :meth:`event_stream` starts. Their
        `event_models` are registered separately by :class:`PluginManager`
        so messages from every source can be validated on the shared path.

        Args:
            listener: The async event source to add to the merged stream.
        """
        self._listeners.append(_ListenerRegistration(listener))

    async def _pump(self, listener: EventListener) -> None:
        """Forward one listener's messages and relay stream-wide stop requests.

        A normal return simply ends this listener's task; it does not end the
        merged stream. `StopStreaming` places the manager's end-of-stream
        sentinel in the shared queue. Any other exception is logged and
        isolated to this listener. Cancellation is allowed to propagate so
        the manager can await task completion during cleanup.

        Args:
            listener: The event source whose async iterator is being consumed.
        """
        try:
            async for message in listener.listen():
                await self._event_queue.put(message)
        except StopStreaming:
            logger.debug("Event listener requested to stop streaming.")
            await self._event_queue.put(_END_OF_STREAM)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception(
                "Unexpected error in listener %s. Stopping just this listener.", listener
            )
            try:
                await listener.stop()
            except Exception:
                logger.exception("Failed to stop listener %s after its failure.", listener)

    async def stop(self) -> None:
        """Stop all listeners and wait for their tasks to finish.

        This method is safe to call after :meth:`event_stream` has already
        performed its cleanup. Every listener's `stop` hook is attempted,
        even if another hook fails.

        Raises:
            ExceptionGroup: One or more ordinary listener cleanup failures.
            BaseException: A cancellation or other non-`Exception` cleanup failure.
        """
        if self._cleanup_started:
            return

        self._cleanup_started = True
        ordinary_errors: list[Exception] = []
        first_base_exception: BaseException | None = None

        for result_errors in await asyncio.gather(
            *(registration.cleanup() for registration in self._listeners),
            return_exceptions=True,
        ):
            for error in (
                [result_errors] if isinstance(result_errors, BaseException) else result_errors
            ):
                logger.error(
                    "Listener cleanup failed: %s",
                    error,
                    exc_info=(type(error), error, error.__traceback__),
                )
                if isinstance(error, Exception):
                    ordinary_errors.append(error)
                elif first_base_exception is None:
                    first_base_exception = error

        if first_base_exception is not None:
            # Raise this after the loop to allow all errors to be logged
            raise first_base_exception
        if ordinary_errors:
            raise ExceptionGroup("Event listener cleanup failed", ordinary_errors)

    async def event_stream(self) -> AsyncIterator[str | bytes]:
        """Start the listeners and yield their messages until shutdown.

        Each listener runs concurrently in an asyncio task. Messages from all
        sources are yielded as they arrive. A listener ending normally does
        not stop the stream, including when all listeners have ended; the
        stream remains available for a later stop request. Raising
        :class:`StopStreaming` from any listener ends the stream and triggers
        cleanup. Cancellation and exceptions also trigger cleanup before they
        propagate.

        Yields:
            The `str` or `bytes` message emitted by a registered listener.

        Raises:
            BaseException: Propagates cancellation or errors raised during
                stream processing or cleanup.
            ExceptionGroup: One or more ordinary listener cleanup failures.
        """
        logger.info("Starting event stream.")
        primary_error: BaseException | None = None
        try:
            for registration in self._listeners:
                registration.task = asyncio.create_task(
                    self._pump(registration.listener),
                    name=f"event-listener-{type(registration.listener).__name__}",
                )
            while True:
                item = await self._event_queue.get()
                if item is _END_OF_STREAM:
                    break
                if not isinstance(item, (str, bytes)):
                    raise TypeError(f"Unexpected event queue item: {item!r}")
                yield item
        except BaseException as exc:
            primary_error = exc
            raise
        finally:
            try:
                await self.stop()
            except BaseException:
                if primary_error is None:
                    raise


class EventListener(ABC):
    """Base class for async sources of plugin events.

    Subclasses yield JSON messages as strings or bytes from :meth:`listen` and
    declare the event models those messages may represent in `event_models`.
    The :class:`EventListenerManager` runs each listener as an asyncio task and
    merges its output with messages from other listeners. Implementations that
    wait for input should use cancellable async I/O and release resources in
    `stop` or in a `finally` block.
    """

    event_models: ClassVar[list[type[EventBase]]]
    """Event models this listener can yield.

    The plugin manager adds these models to its event adapter so listener
    messages can be validated and dispatched alongside built-in events. Each
    listener subclass should define this list.
    """

    @abstractmethod
    def listen(self) -> AsyncIterator[str | bytes]:
        """Listen for events and yield each message as it arrives.

        This method must return an async iterator yielding JSON strings or
        bytes. It is consumed in a task managed by :class:`EventListenerManager`;
        implementations should avoid blocking the event loop and should use
        awaitable, cancellable operations for I/O.

        Yields:
            A JSON message that can be validated against `event_models`.

        Raises:
            StopStreaming: To request termination of the entire merged stream.
            asyncio.CancelledError: When the runtime is shutting down.
        """

    @abstractmethod
    async def stop(self) -> None:
        """Stop the listener and release resources it owns.

        The event listener manager calls this during normal stream termination
        and cancellation, then waits for the listener task to finish. This
        hook must be safe to call repeatedly and after partial startup. It
        should release resources even when the listener's iterator is blocked
        on I/O.
        """
