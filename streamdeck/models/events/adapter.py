from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Union

from pydantic import Field, TypeAdapter

from streamdeck.models.events import DEFAULT_EVENT_MODELS
from streamdeck.models.events.application import ApplicationDidLaunch, ApplicationDidTerminate
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
    from streamdeck.models.events.base import EventBase


## Default event models and names.


event_adapter: TypeAdapter[EventBase] = TypeAdapter(
    Annotated[
        Union[  # noqa: UP007
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
        ],
        Field(discriminator="event")
    ]
)


## EventAdapter class for handling and extending available event models.

class EventAdapter:
    """TypeAdapter-encompassing class for handling and extending available event models."""
    def __init__(self) -> None:
        self._models: list[type[EventBase]] = []
        self._type_adapter: TypeAdapter[EventBase] | None = None

        self._event_names: set[str] = set()
        """A set of all event names that have been registered with the adapter.
        This set starts out containing the default event models defined by the library.
        """

        for model in DEFAULT_EVENT_MODELS:
            self.add_model(model)

    def add_model(self, model: type[EventBase]) -> None:
        """Add a model to the adapter, and add the event name of the model to the set of registered event names."""
        self._models.append(model)
        self._event_names.update(model.get_model_event_name())

    def event_name_exists(self, event_name: str) -> bool:
        """Check if an event name has been registered with the adapter."""
        return event_name in self._event_names

    @property
    def type_adapter(self) -> TypeAdapter[EventBase]:
        """Get the TypeAdapter instance for the event models."""
        if self._type_adapter is None:
            self._type_adapter = TypeAdapter(
                Annotated[
                    Union[tuple(self._models)],  # noqa: UP007
                    Field(discriminator="event")
                ]
            )

        return self._type_adapter

    def validate_json(self, data: str | bytes) -> EventBase:
        """Validate a JSON string or bytes object as an event model."""
        return self.type_adapter.validate_json(data)

