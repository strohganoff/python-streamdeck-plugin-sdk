from typing import Literal

from streamdeck.models.events.base import EventBase


class DidReceiveDeepLink(EventBase):
    event: Literal["didReceiveDeepLink"]  # type: ignore[override]
    payload: dict[Literal["url"], str]
