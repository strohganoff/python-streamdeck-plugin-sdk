from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field

from streamdeck.models.events.base import ConfiguredBaseModel, EventBase
from streamdeck.models.events.common import (
    CardinalityDiscriminated,
    ContextualEventMixin,
    DeviceSpecificEventMixin,
    MultiActionPayload,
    PluginDefinedData,
    SingleActionPayload,
)


class DidReceiveSettings(EventBase, ContextualEventMixin, DeviceSpecificEventMixin):
    """Occurs when the settings associated with an action instance are requested, or when the the settings were updated by the property inspector."""
    event: Literal["didReceiveSettings"]  # type: ignore[override]
    payload: CardinalityDiscriminated[SingleActionPayload, MultiActionPayload]
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
