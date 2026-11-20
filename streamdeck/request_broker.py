"""Correlate asynchronous Stream Deck command requests with response events."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from logging import getLogger
from typing import TYPE_CHECKING, Generic, Protocol, TypeVar, cast
from uuid import uuid4

from streamdeck.models.events import EventBase


if TYPE_CHECKING:
    from pydantic import JsonValue


logger = getLogger("streamdeck.request_broker")

ResponseEventT = TypeVar("ResponseEventT", bound=EventBase)


@dataclass
class _PendingRequest(Generic[ResponseEventT]):
    response_type: type[ResponseEventT]
    context: str | None
    future: asyncio.Future[ResponseEventT]


class AsyncEventSender(Protocol):
    """Narrow transport capability used by the request broker."""

    async def send_event(self, data: dict[str, JsonValue]) -> None: ...


class RequestBroker:
    """Send Stream Deck commands and correlate response events by request ID.

    The broker observes validated events from the runtime's event router. It
    forwards outbound messages through its sender, but does not read from the
    WebSocket or consume events from normal dispatch.
    """

    def __init__(self, sender: AsyncEventSender) -> None:
        self._sender = sender
        self._pending: dict[str, _PendingRequest[EventBase]] = {}

    async def send_event(self, data: dict[str, JsonValue]) -> None:
        """Send a one-way command through the active WebSocket transport."""
        await self._sender.send_event(data)

    async def request(
        self,
        *,
        response_type: type[ResponseEventT],
        context: str | None,
        command: dict[str, JsonValue],
        timeout: float | None,
    ) -> ResponseEventT:
        """Register a waiter, send its command, and await its matching event.

        The waiter is installed before ``send`` is awaited so an immediate
        response cannot arrive before the request is registered.
        """
        if timeout is not None and timeout <= 0:
            raise ValueError("timeout must be greater than zero or None")

        request_id = uuid4().hex
        future: asyncio.Future[ResponseEventT] = asyncio.get_running_loop().create_future()
        pending = _PendingRequest(
            response_type=response_type,
            context=context,
            future=future,
        )
        self._pending[request_id] = cast("_PendingRequest[EventBase]", pending)

        try:
            await self.send_event({**command, "id": request_id})
            if timeout is None:
                return await future
            try:
                return await asyncio.wait_for(future, timeout)
            except asyncio.TimeoutError as exc:
                msg = f"Timed out waiting for {response_type.__name__} (request id {request_id})."
                raise TimeoutError(msg) from exc
        finally:
            self._pending.pop(request_id, None)
            if not future.done():
                future.cancel()

    def resolve(self, event: EventBase) -> bool:
        """Resolve the matching request, if this event carries its request ID."""
        request_id = getattr(event, "id", None)
        if not isinstance(request_id, str):
            return False

        pending = self._pending.get(request_id)
        if pending is None:
            return False

        if not isinstance(event, pending.response_type):
            logger.warning(
                "Response event %s did not match request %s expecting %s.",
                event.event,
                request_id,
                pending.response_type.__name__,
            )
            return False

        if pending.context is not None and getattr(event, "context", None) != pending.context:
            logger.warning("Response event context did not match request %s.", request_id)
            return False

        if pending.future.done():
            return False

        pending.future.set_result(cast("ResponseEventT", event))
        return True

    def fail_all(self, error: Exception) -> None:
        """Fail every outstanding request, such as when the runtime shuts down."""
        pending_requests = list(self._pending.values())
        self._pending.clear()
        for pending in pending_requests:
            if not pending.future.done():
                pending.future.set_exception(error)
