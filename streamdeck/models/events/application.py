from __future__ import annotations

from typing import Literal

from streamdeck.models.events.base import EventBase


## EventBase implementation models of the Stream Deck Plugin SDK events.

class ApplicationDidLaunch(EventBase):
    """Occurs when a monitored application is launched."""
    event: Literal["applicationDidLaunch"]  # type: ignore[override]
    payload: dict[Literal["application"], str]
    """Payload containing the name of the application that triggered the event."""


class ApplicationDidTerminate(EventBase):
    """Occurs when a monitored application terminates."""
    event: Literal["applicationDidTerminate"]  # type: ignore[override]
    payload: dict[Literal["application"], str]
    """Payload containing the name of the application that triggered the event."""
