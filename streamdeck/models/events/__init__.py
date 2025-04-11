"""Stream Deck Event Models.

These models are used to represent the events that can be received by the Stream Deck SDK plugin.
The "default" events are those passed from the Stream Deck software itself, but custom events can
be created by the plugin developer and listened for in the same way.

The events are organized into the same categories as the Stream Deck SDK documentation defines them.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from streamdeck.models.events.application import ApplicationDidLaunch, ApplicationDidTerminate
from streamdeck.models.events.base import EventBase
from streamdeck.models.events.deep_link import DidReceiveDeepLink
from streamdeck.models.events.devices import DeviceDidConnect, DeviceDidDisconnect
from streamdeck.models.events.dials import DialDown, DialRotate, DialUp
from streamdeck.models.events.keys import KeyDown, KeyUp
from streamdeck.models.events.property_inspector import (
    DidReceivePropertyInspectorMessage,
    PropertyInspectorDidAppear,
    PropertyInspectorDidDisappear,
)
from streamdeck.models.events.settings import DidReceiveGlobalSettings, DidReceiveSettings
from streamdeck.models.events.system import SystemDidWakeUp
from streamdeck.models.events.title_parameters import TitleParametersDidChange
from streamdeck.models.events.touch_tap import TouchTap
from streamdeck.models.events.visibility import WillAppear, WillDisappear


if TYPE_CHECKING:
    from typing import Final

    from streamdeck.types import LiteralStrGenericAlias


DEFAULT_EVENT_MODELS: Final[list[type[EventBase[LiteralStrGenericAlias]]]] = [
    ApplicationDidLaunch,
    ApplicationDidTerminate,
    DeviceDidConnect,
    DeviceDidDisconnect,
    DialDown,
    DialRotate,
    DialUp,
    DidReceiveDeepLink,
    KeyUp,
    KeyDown,
    DidReceivePropertyInspectorMessage,
    PropertyInspectorDidAppear,
    PropertyInspectorDidDisappear,
    DidReceiveGlobalSettings,
    DidReceiveSettings,
    SystemDidWakeUp,
    TitleParametersDidChange,
    TouchTap,
    WillAppear,
    WillDisappear,
]


def _get_default_event_names() -> set[str]:
    default_event_names: set[str] = set()

    for event_model in DEFAULT_EVENT_MODELS:
        default_event_names.update(event_model.get_model_event_names())

    return default_event_names


DEFAULT_EVENT_NAMES: Final[set[str]] = _get_default_event_names()



__all__ = [
    "DEFAULT_EVENT_MODELS",
    "DEFAULT_EVENT_NAMES",
    "ApplicationDidLaunch",
    "ApplicationDidTerminate",
    "DeviceDidConnect",
    "DeviceDidDisconnect",
    "DialDown",
    "DialRotate",
    "DialUp",
    "DidReceiveDeepLink",
    "DidReceiveGlobalSettings",
    "DidReceivePropertyInspectorMessage",
    "DidReceiveSettings",
    "EventBase",
    "KeyDown",
    "KeyUp",
    "PropertyInspectorDidAppear",
    "PropertyInspectorDidDisappear",
    "SystemDidWakeUp",
    "TitleParametersDidChange",
    "TouchTap",
    "WillAppear",
    "WillDisappear",
]
