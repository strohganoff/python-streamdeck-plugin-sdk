"""Process a stream of validated events with sequential dispatch."""

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


_END_DISPATCH = sentinel("_END_DISPATCH")


class EventStreamProcessor:
    """Read events concurrently with sequential dispatch."""

    def __init__(
        self,
        dispatch: Callable[[EventBase], Awaitable[None]],
    ) -> None:
        self._dispatch = dispatch

    async def _route_events(
        self,
        events: AsyncGenerator[EventBase, None],
        dispatch_queue: asyncio.Queue[object],
    ) -> None:
        """Queue validated events in stream order."""
        async with aclosing(events):
            async for event in events:
                await dispatch_queue.put(event)
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
