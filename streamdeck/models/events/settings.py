from __future__ import annotations

from typing import Literal

from streamdeck.models.events.base import ConfiguredBaseModel, EventBase
from streamdeck.models.events.common import (
    ActionInstancePayloadEventMixin,
    BasePayload,
    CardinalityDiscriminated,
    CoordinatesPayloadMixin,
    DeviceSpecificEventMixin,
    KeypadControllerType,
    MultiActionPayloadMixin,
    SettingsPayloadMixin,
    SingleActionPayloadMixin,
    StatefulActionPayloadMixin,
)


## Models for didReceiveSettings event and its specific payloads.


class SingleActionSettingsPayload(
    BasePayload,
    SingleActionPayloadMixin,
    StatefulActionPayloadMixin,
    CoordinatesPayloadMixin,
):
    """Action-instance event data for a didReceiveSettings events that are not part of a multi-action."""


class MultiActionSettingsPayload(
    BasePayload[KeypadControllerType],
    MultiActionPayloadMixin,
    StatefulActionPayloadMixin,
):
    """Action-instance event data for a didReceiveSettings events that are part of a multi-action.

    NOTE: Action instances that are part of a multi-action are only applicable to the 'Keypad' controller type.
    """


class DidReceiveSettings(EventBase[Literal["didReceiveSettings"]], ActionInstancePayloadEventMixin[CardinalityDiscriminated[SingleActionSettingsPayload, MultiActionSettingsPayload]], DeviceSpecificEventMixin):  # fmt: skip
    """Occurs when the settings associated with an action instance are requested, or when the the settings were updated by the property inspector."""

    payload: CardinalityDiscriminated[SingleActionSettingsPayload, MultiActionSettingsPayload]
    """Action-instance event data for this event."""


## Models for didReceiveGlobalSettings event and its specific payload.


class GlobalSettingsPayload(ConfiguredBaseModel, SettingsPayloadMixin):
    """Additional information about the didReceiveGlobalSettings event that occurred."""


class DidReceiveGlobalSettings(EventBase[Literal["didReceiveGlobalSettings"]]):
    """Occurs when the plugin receives the global settings from the Stream Deck."""

    payload: GlobalSettingsPayload
    """Additional information about the event that occurred."""
