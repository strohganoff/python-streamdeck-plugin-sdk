from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, ClassVar, cast

import pytest

from streamdeck.event_listener import EventListener, EventListenerManager, StopStreaming
from streamdeck.models.events import ApplicationDidLaunch, EventBase


if TYPE_CHECKING:
    from collections.abc import AsyncIterator


class ListListener(EventListener):
    event_models: ClassVar[list[type[EventBase]]] = [ApplicationDidLaunch]

    def __init__(self, events: list[str], *, delay: float = 0) -> None:
        self.events = events
        self.delay = delay
        self.stopped = False

    async def listen(self) -> AsyncIterator[str]:
        for event in self.events:
            if self.delay:
                await asyncio.sleep(self.delay)
            yield event

    async def stop(self) -> None:
        self.stopped = True


class StopListener(ListListener):
    async def listen(self) -> AsyncIterator[str]:
        raise StopStreaming
        yield "unreachable"


def test_multiple_listeners_merge_and_cleanup() -> None:
    async def scenario() -> None:
        manager = EventListenerManager()
        first = ListListener(["a", "b"])
        second = ListListener(["c", "d"], delay=0.001)
        manager.add_listener(first)
        manager.add_listener(second)
        events: list[str] = []
        async for event in manager.event_stream():
            events.append(event)
            if len(events) == 4:
                break
        await manager.stop()
        assert set(events) == {"a", "b", "c", "d"}
        assert first.stopped and second.stopped

    asyncio.run(scenario())


def test_stop_streaming_ends_the_merged_stream() -> None:
    class CountingStopListener(StopListener):
        def __init__(self) -> None:
            super().__init__([])
            self.stop_calls = 0

        async def stop(self) -> None:
            self.stop_calls += 1
            await super().stop()

    async def scenario() -> None:
        manager = EventListenerManager()
        listener = CountingStopListener()
        manager.add_listener(listener)
        assert [event async for event in manager.event_stream()] == []
        await manager.stop()
        assert listener.stop_calls == 1

    asyncio.run(scenario())


def test_cleanup_attempts_every_listener_when_a_stop_hook_fails() -> None:
    class FailingStopListener(ListListener):
        def __init__(self) -> None:
            super().__init__([])
            self.stop_calls = 0

        async def stop(self) -> None:
            self.stop_calls += 1
            raise RuntimeError("stop failed")

    async def scenario() -> None:
        manager = EventListenerManager()
        manager.add_listener(StopListener([]))
        failing_listener = FailingStopListener()
        other_listener = ListListener([])
        manager.add_listener(failing_listener)
        manager.add_listener(other_listener)

        with pytest.raises(Exception, match="Event listener cleanup failed") as exc_info:
            async for _ in manager.event_stream():
                pass

        assert type(exc_info.value).__name__ == "ExceptionGroup"
        assert [str(error) for error in exc_info.value.exceptions] == ["stop failed"]
        assert failing_listener.stop_calls == 1
        assert other_listener.stopped

    asyncio.run(scenario())


def test_stop_groups_multiple_listener_cleanup_errors() -> None:
    class FailingStopListener(ListListener):
        def __init__(self, message: str) -> None:
            super().__init__([])
            self.message = message

        async def stop(self) -> None:
            raise RuntimeError(self.message)

    async def scenario() -> None:
        manager = EventListenerManager()
        manager.add_listener(FailingStopListener("first stop failed"))
        manager.add_listener(FailingStopListener("second stop failed"))

        with pytest.raises(Exception, match="Event listener cleanup failed") as exc_info:
            await manager.stop()

        assert type(exc_info.value).__name__ == "ExceptionGroup"
        assert [str(error) for error in exc_info.value.exceptions] == [
            "first stop failed",
            "second stop failed",
        ]

    asyncio.run(scenario())


def test_event_stream_groups_multiple_listener_cleanup_errors() -> None:
    class FailingStopListener(ListListener):
        def __init__(self, message: str) -> None:
            super().__init__([])
            self.message = message

        async def stop(self) -> None:
            raise RuntimeError(self.message)

    async def scenario() -> None:
        manager = EventListenerManager()
        manager.add_listener(StopListener([]))
        manager.add_listener(FailingStopListener("first stop failed"))
        manager.add_listener(FailingStopListener("second stop failed"))

        with pytest.raises(Exception, match="Event listener cleanup failed") as exc_info:
            async for _ in manager.event_stream():
                pass

        assert type(exc_info.value).__name__ == "ExceptionGroup"
        assert [str(error) for error in exc_info.value.exceptions] == [
            "first stop failed",
            "second stop failed",
        ]

    asyncio.run(scenario())


def test_event_stream_error_is_preserved_when_cleanup_fails() -> None:
    class FailingStopListener(ListListener):
        async def stop(self) -> None:
            raise RuntimeError("cleanup failed")

    async def scenario() -> None:
        manager = EventListenerManager()
        manager.add_listener(FailingStopListener([]))
        manager.add_listener(FailingStopListener([]))
        manager._event_queue.put_nowait(cast(str, 123))

        with pytest.raises(TypeError, match="Unexpected event queue item"):
            async for _ in manager.event_stream():
                pass

    asyncio.run(scenario())


def test_cleanup_does_not_group_base_exceptions() -> None:
    class CancelledStopListener(ListListener):
        async def stop(self) -> None:
            raise asyncio.CancelledError

    class FailingStopListener(ListListener):
        async def stop(self) -> None:
            raise RuntimeError("ordinary cleanup failure")

    async def scenario() -> None:
        manager = EventListenerManager()
        manager.add_listener(CancelledStopListener([]))
        manager.add_listener(FailingStopListener([]))

        with pytest.raises(asyncio.CancelledError):
            await manager.stop()

    asyncio.run(scenario())


def test_normal_completion_does_not_end_stream_and_stop_cancels_waiter() -> None:
    async def scenario() -> None:
        manager = EventListenerManager()
        listener = ListListener(["once"])
        manager.add_listener(listener)
        stream = manager.event_stream()
        assert await anext(stream) == "once"
        pending = asyncio.create_task(anext(stream))
        try:
            await asyncio.wait_for(asyncio.shield(pending), timeout=0.01)
        except asyncio.TimeoutError:
            pass
        else:
            raise AssertionError("A normally completed listener must not end the stream.")
        await manager.stop()
        pending.cancel()
        try:
            await pending
        except (asyncio.CancelledError, StopAsyncIteration):
            pass
        await stream.aclose()
        assert listener.stopped

    asyncio.run(scenario())


def test_listener_failure_isolated_and_logged() -> None:
    class FailingListener(ListListener):
        async def listen(self) -> AsyncIterator[str]:
            raise ValueError("broken")
            yield "unreachable"

    async def scenario() -> None:
        manager = EventListenerManager()
        manager.add_listener(FailingListener([]))
        survivor = ListListener(["survived"])
        manager.add_listener(survivor)
        stream = manager.event_stream()
        assert await anext(stream) == "survived"
        await stream.aclose()
        assert survivor.stopped

    asyncio.run(scenario())
