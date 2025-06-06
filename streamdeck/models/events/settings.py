from __future__ import annotations

from streamdeck.models.events.base import ConfiguredBaseModel, EventBase
from streamdeck.models.events.common import (
    BasePayload,
    CardinalityDiscriminated,
    ContextualEventMixin,
    CoordinatesPayloadMixin,
    DeviceSpecificEventMixin,
    KeypadControllerType,
    MultiActionPayloadMixin,
    SingleActionPayloadMixin,
    StatefulActionPayloadMixin,
)
from streamdeck.types import PluginDefinedData  # noqa: TC001


## Models for didReceiveSettings event and its specific payloads.


class SingleActionSettingsPayload(
    BasePayload,
    SingleActionPayloadMixin,
    StatefulActionPayloadMixin,
    CoordinatesPayloadMixin,
):
    """Contextualized information for a didReceiveSettings events that are not part of a multi-action."""


class MultiActionSettingsPayload(
    BasePayload[KeypadControllerType],
    MultiActionPayloadMixin,
    StatefulActionPayloadMixin,
):
    """Contextualized information for a didReceiveSettings events that are part of a multi-action.

    NOTE: Action instances that are part of a multi-action are only applicable to the 'Keypad' controller type.
    """


class DidReceiveSettings(EventBase["didReceiveSettings"], ContextualEventMixin, DeviceSpecificEventMixin):
    """Occurs when the settings associated with an action instance are requested, or when the the settings were updated by the property inspector."""
    payload: CardinalityDiscriminated[SingleActionSettingsPayload, MultiActionSettingsPayload]
    """Contextualized information for this event."""


## Models for didReceiveGlobalSettings event and its specific payload.

class GlobalSettingsPayload(ConfiguredBaseModel):
    """Additional information about the didReceiveGlobalSettings event that occurred."""
    settings: PluginDefinedData
    """The global settings received from the Stream Deck."""


class DidReceiveGlobalSettings(EventBase["didReceiveGlobalSettings"]):
    """Occurs when the plugin receives the global settings from the Stream Deck."""
    payload: GlobalSettingsPayload
    """Additional information about the event that occurred."""
