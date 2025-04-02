from __future__ import annotations

from typing import Literal

from streamdeck.models.events.base import EventBase


## EventBase implementation models of the Stream Deck Plugin SDK events.

class ApplicationDidLaunch(EventBase):
    event: Literal["applicationDidLaunch"]  # type: ignore[override]
    payload: dict[Literal["application"], str]
    """Payload containing the name of the application that triggered the event."""


class ApplicationDidTerminate(EventBase):
    event: Literal["applicationDidTerminate"]  # type: ignore[override]
    payload: dict[Literal["application"], str]
    """Payload containing the name of the application that triggered the event."""
