from __future__ import annotations

from typing import Literal

from streamdeck.models.events.base import ConfiguredBaseModel, EventBase
from streamdeck.models.events.common import (
    BaseActionPayload,
    CardinalityDiscriminated,
    ContextualEventMixin,
    CoordinatesPayloadMixin,
    DeviceSpecificEventMixin,
    KeypadControllerType,
    MultiActionPayloadMixin,
    PluginDefinedData,
    SingleActionPayloadMixin,
)


## Models for didReceiveSettings event and its specific payloads.

class SingleActionSettingsPayload(BaseActionPayload, SingleActionPayloadMixin, CoordinatesPayloadMixin):
    """Contextualized information for a didReceiveSettings events that are not part of a multi-action."""


class MultiActionSettingsPayload(BaseActionPayload[KeypadControllerType], MultiActionPayloadMixin):
    """Contextualized information for a didReceiveSettings events that are part of a multi-action.

    NOTE: Action instances that are part of a multi-action are only applicable to the 'Keypad' controller type.
    """


class DidReceiveSettings(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    """Occurs when the settings associated with an action instance are requested, or when the the settings were updated by the property inspector."""
    event: Literal["didReceiveSettings"]  # type: ignore[override]
    payload: CardinalityDiscriminated[SingleActionSettingsPayload, MultiActionSettingsPayload]
    """Contextualized information for this event."""


## Models for didReceiveGlobalSettings event and its specific payload.

class GlobalSettingsPayload(ConfiguredBaseModel):
    """Additional information about the didReceiveGlobalSettings event that occurred."""
    settings: PluginDefinedData
    """The global settings received from the Stream Deck."""


class DidReceiveGlobalSettings(EventBase):
    """Occurs when the plugin receives the global settings from the Stream Deck."""
    event: Literal["didReceiveGlobalSettings"]  # type: ignore[override]
    payload: GlobalSettingsPayload
    """Additional information about the event that occurred."""
