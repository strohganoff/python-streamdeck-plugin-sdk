from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from typing_extensions import TypeAlias  # noqa: UP035

from streamdeck.models.events import EventBase


EventHandlerFunc: TypeAlias = Callable[[EventBase], None]  # noqa: UP040


EventNameStr: TypeAlias = Literal[  # noqa: UP040
    "applicationDidLaunch",
    "applicationDidTerminate",
    "deviceDidConnect",
    "deviceDidDisconnect",
    "dialDown",
    "dialRotate",
    "dialUp",
    "didReceiveGlobalSettings",
    "didReceiveDeepLink",
    "didReceiveSettings",
    "keyDown",
    "keyUp",
    "propertyInspectorDidAppear",
    "propertyInspectorDidDisappear",
    "systemDidWakeUp",
    "titleParametersDidChange",
    "touchTap",
    "willAppear",
    "willDisappear"
]
