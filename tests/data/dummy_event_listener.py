from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from streamdeck.event_listener import EventListener
from streamdeck.models.events import EventBase
from typing_extensions import override  # noqa: UP035


if TYPE_CHECKING:
    from collections.abc import Generator
    from typing import Any, ClassVar


class DummyEvent(EventBase):
    """A dummy event for testing purposes."""
    event: Literal["dummy"]  # type: ignore[assignment]
    something: int


class DummyEventListener(EventListener):
    """A dummy event listener for testing purposes."""
    event_models: ClassVar[list[type[EventBase]]] = [DummyEvent]

    @override
    def listen(self) -> Generator[str | bytes, Any, None]:
        """Yields a dummy event."""
        yield '{"event": "dummy", "something": 42}'

    @override
    def stop(self) -> None:
        """Doesn't do anything."""
