"""Route validated events to request waiters and sequential handlers."""

from __future__ import annotations

import asyncio
import sys
from contextlib import aclosing
from typing import TYPE_CHECKING

from typing_extensions import sentinel

from streamdeck.models.events import EventBase


if sys.version_info >= (3, 11):
    from asyncio import TaskGroup
else:
    from taskgroup import TaskGroup


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Awaitable, Callable

    from streamdeck.request_broker import RequestBroker


_END_DISPATCH = sentinel("_END_DISPATCH")


class EventStreamProcessor:
    """Coordinate response routing and sequential event dispatch."""

    def __init__(
        self,
        request_broker: RequestBroker,
        dispatch: Callable[[EventBase], Awaitable[None]],
    ) -> None:
        self._request_broker = request_broker
        self._dispatch = dispatch

    async def _route_events(
        self,
        events: AsyncGenerator[EventBase, None],
        dispatch_queue: asyncio.Queue[object],
    ) -> None:
        """Resolve response waiters, then queue events for normal dispatch."""
        try:
            async with aclosing(events):
                async for event in events:
                    self._request_broker.resolve(event)
                    await dispatch_queue.put(event)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self._request_broker.fail_all(exc)
            raise
        else:
            self._request_broker.fail_all(
                RuntimeError("The event stream ended before the request completed.")
            )
            await dispatch_queue.put(_END_DISPATCH)

    async def _dispatch_events(self, dispatch_queue: asyncio.Queue[object]) -> None:
        """Dispatch queued events one at a time, awaiting each handler."""
        while True:
            item = await dispatch_queue.get()

            if item is _END_DISPATCH:
                return
            if not isinstance(item, EventBase):
                raise TypeError(f"Unexpected dispatch queue item: {item!r}")

            await self._dispatch(item)

    async def run(self, events: AsyncGenerator[EventBase, None]) -> None:
        """Route events concurrently and dispatch them sequentially.

        Raises:
            ExceptionGroup: If event routing or dispatch fails.
        """
        dispatch_queue: asyncio.Queue[object] = asyncio.Queue()
        async with TaskGroup() as tasks:
            tasks.create_task(
                self._route_events(events, dispatch_queue),
                name="plugin-event-router",
            )
            tasks.create_task(
                self._dispatch_events(dispatch_queue),
                name="plugin-event-dispatcher",
            )
