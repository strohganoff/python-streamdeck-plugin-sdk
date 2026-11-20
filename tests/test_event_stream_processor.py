from __future__ import annotations

import asyncio
import sys
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

import pytest

from streamdeck.event_stream_processor import EventStreamProcessor
from streamdeck.request_broker import AsyncEventSender, RequestBroker
from tests.test_utils.fake_event_factories import KeyDownEventFactory


if sys.version_info < (3, 11):
    from exceptiongroup import ExceptionGroup

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from streamdeck.models.events import EventBase


def test_processor_reads_ahead_and_dispatches_in_order() -> None:
    async def scenario() -> None:
        first, second = KeyDownEventFactory.batch(2)
        source_drained = asyncio.Event()
        handled: list[EventBase] = []

        async def events() -> AsyncGenerator[EventBase, None]:
            yield first
            yield second
            source_drained.set()

        async def dispatch(event: EventBase) -> None:
            if event is first:
                await source_drained.wait()
                assert not handled
            handled.append(event)

        processor = EventStreamProcessor(RequestBroker(AsyncMock(spec=AsyncEventSender)), dispatch)
        await asyncio.wait_for(processor.run(events()), timeout=1)
        assert handled == [first, second]

    asyncio.run(scenario())


def test_dispatch_failure_closes_the_event_source() -> None:
    async def scenario() -> None:
        error = RuntimeError("dispatch failed")
        source_closed = asyncio.Event()

        async def events() -> AsyncGenerator[EventBase, None]:
            try:
                yield KeyDownEventFactory.build()
                await asyncio.Event().wait()
            finally:
                source_closed.set()

        async def dispatch(_event: EventBase) -> None:
            raise error

        processor = EventStreamProcessor(RequestBroker(AsyncMock(spec=AsyncEventSender)), dispatch)
        with pytest.raises(ExceptionGroup) as captured:
            await asyncio.wait_for(processor.run(events()), timeout=1)

        assert captured.value.exceptions == (error,)
        assert source_closed.is_set()

    asyncio.run(scenario())
