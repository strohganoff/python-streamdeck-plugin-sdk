from __future__ import annotations

import asyncio
from typing import Literal
from unittest.mock import AsyncMock

import pytest

from streamdeck.models.events import EventBase
from streamdeck.models.events.settings import DidReceiveGlobalSettings
from streamdeck.request_broker import AsyncEventSender, RequestBroker


class CustomEvent(EventBase[Literal["custom"]]):
    id: list[str]


def test_ignore_custom_event_with_non_string_id() -> None:
    broker = RequestBroker(AsyncMock(spec=AsyncEventSender))
    assert not broker.resolve(CustomEvent(event="custom", id=["not a request ID"]))


def test_timeout_raises_builtin_error_with_request_details() -> None:
    async def scenario() -> None:
        sender = AsyncMock(spec=AsyncEventSender)
        broker = RequestBroker(sender)
        with pytest.raises(TimeoutError, match="Timed out waiting for DidReceiveGlobalSettings"):
            await broker.request(
                response_type=DidReceiveGlobalSettings,
                context=None,
                command={"event": "getGlobalSettings", "context": "registration"},
                timeout=0.01,
            )

        request_id = sender.send_event.await_args.args[0]["id"]
        event = DidReceiveGlobalSettings.model_validate({
            "event": "didReceiveGlobalSettings",
            "id": request_id,
            "payload": {"settings": {}},
        })
        assert not broker.resolve(event)

    asyncio.run(scenario())
