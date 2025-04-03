from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from streamdeck.models.events.base import EventBase


class ApplicationPayload(BaseModel):
    """Payload containing the name of the application that triggered the event."""
    application: str
    """Name of the application that triggered the event."""


class ApplicationDidLaunch(EventBase):
    """Occurs when a monitored application is launched."""
    event: Literal["applicationDidLaunch"]  # type: ignore[override]
    payload: ApplicationPayload
    """Payload containing the name of the application that triggered the event."""


class ApplicationDidTerminate(EventBase):
    """Occurs when a monitored application terminates."""
    event: Literal["applicationDidTerminate"]  # type: ignore[override]
    payload: ApplicationPayload
    """Payload containing the name of the application that triggered the event."""
