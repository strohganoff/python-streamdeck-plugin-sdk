from __future__ import annotations

from typing import Literal

from streamdeck.models.events.base import ConfiguredBaseModel, EventBase


class ApplicationPayload(ConfiguredBaseModel):
    """Payload containing the name of the application that triggered the event."""
    application: str
    """Name of the application that triggered the event."""


class ApplicationDidLaunch(EventBase[Literal["applicationDidLaunch"]]):
    """Occurs when a monitored application is launched."""
    payload: ApplicationPayload
    """Payload containing the name of the application that triggered the event."""


class ApplicationDidTerminate(EventBase[Literal["applicationDidTerminate"]]):
    """Occurs when a monitored application terminates."""
    payload: ApplicationPayload
    """Payload containing the name of the application that triggered the event."""
