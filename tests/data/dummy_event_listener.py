from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from typing_extensions import override  # noqa: UP035

from streamdeck.event_listener import EventListener
from streamdeck.models.events import EventBase


if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import ClassVar


class DummyEvent(EventBase[Literal["dummy"]]):
    """A dummy event for testing purposes."""

    something: int


class DummyEventListener(EventListener):
    """A dummy event listener for testing purposes."""

    event_models: ClassVar[list[type[EventBase]]] = [DummyEvent]

    @override
    def listen(self) -> Iterator[str | bytes]:
        """Yields a dummy event."""
        yield '{"event": "dummy", "something": 42}'

    @override
    def stop(self) -> None:
        """Doesn't do anything."""
