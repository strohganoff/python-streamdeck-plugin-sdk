from __future__ import annotations

from collections.abc import MutableMapping
from typing import (
    TYPE_CHECKING,
    ForwardRef,
    Optional,
    TypeVar,
    get_args,
)

from pydantic import BaseModel, ConfigDict, RootModel

from streamdeck.event_handlers.handler_methods import HandlerMethodCatalogMixin, on
from streamdeck.models.events.common import Coordinates, CoordinatesDict, CoordinatesPayloadMixin
from streamdeck.models.events.devices import DeviceInfo  # noqa: TC001
from streamdeck.types import ActionInstanceUUIDStr, ActionUUIDStr, DeviceUUIDStr, PluginDefinedData


if TYPE_CHECKING:
    from collections.abc import Iterator, KeysView, ValuesView

    from streamdeck.models.events import (
        DeviceDidConnect,
        DeviceDidDisconnect,
        DidReceiveSettings,
        WillAppear,
    )


## Class for holding the plugin state. Not a Singleton

class PluginState(HandlerMethodCatalogMixin):
    """Class for holding the plugin state based on observed events."""

    __slots__ = ("action_instances", "data")

    data: PluginDataDictModel
    action_instances: set[ActionInstanceUUIDStr]

    def __init__(self) -> None:
        """Initialize the plugin state."""
        self.data = PluginDataDictModel()
        self.action_instances = set()

    def _get_action_instance_reference(self, device: DeviceUUIDStr, action: ActionUUIDStr, context: ActionInstanceUUIDStr) -> ActionInstanceDataDictModel:
        """Get (or create a default if it doesn't already exist) a reference to the action instance in the plugin-state data dictionary."""
        return self.data[device].actions[action][context]

    @on("deviceDidConnect")
    def add_device(self, event_data: DeviceDidConnect) -> None:
        """Add a new device to the plugin state when it connects, including its device info."""
        # If the device is already in the data dictionary, we don't need to do anything.
        if event_data.device in self.data:
            return

        # Otherwise, we need to add the device to the data dictionary.
        self.data[event_data.device] = DeviceDataDictModel(
            info=event_data.device_info,
        )

    @on("deviceDidDisconnect")
    def remove_data_for_device(self, event_data: DeviceDidDisconnect) -> None:
        """Remove the device data from the plugin state when the device disconnects."""
        removed_device_data: DeviceDataDictModel | None = self.data.pop(event_data.device, None)

        if removed_device_data is None:
            return

        # Send a set comprehension of all action instance uuids related to the removed device to the `set.difference_update` method
        # to let the C python interpreter handle the set operations much more efficiently than via a python loop.
        action_instance_uuids_to_remove: set[ActionInstanceUUIDStr] = {
            ctx_uuid
            for action in removed_device_data.actions.values()
            for ctx_uuid in action
        }
        self.action_instances.difference_update(action_instance_uuids_to_remove)

    @on("willAppear")
    def set_initial_state(self, event_data: WillAppear) -> None:
        """Set the initial state of the action instance when it appears."""
        action_instance_data_ref: ActionInstanceDataDictModel = self._get_action_instance_reference(
            event_data.device, event_data.action, event_data.context
        )

        action_instance_data_ref.settings = event_data.payload.settings

        # Rather than checking if this is multi-action or single-action, just check if the event payload has coordinates.
        if isinstance(event_data.payload, CoordinatesPayloadMixin):
            action_instance_data_ref.coordinates = event_data.payload.coordinates

        # Add the action instance to the set of action instances.
        self.action_instances.add(event_data.context)

    @on("didReceiveSettings")
    def update_instance_settings(self, event_data: DidReceiveSettings) -> None:
        """Update the settings of the action instance when new settings are received."""
        action_instance_data_ref: ActionInstanceDataDictModel = self._get_action_instance_reference(
            event_data.device, event_data.action, event_data.context
        )
        action_instance_data_ref.settings = event_data.payload.settings


## Nested models for the plugin data dictionary used to track state in the plugin.

K = TypeVar("K", bound=str)
V = TypeVar("V")

# TypeVar for a default type to be popped from the dictionary in the pop method.
D = TypeVar("D")


class RootDefaultDictModel(RootModel[dict[K, V]], MutableMapping[K, V]):
    """A generic base class for RootModels that provides a defaultdict-like access interface.

    This class provides a default dictionary-like access interface to the root object.
    """
    @property
    def value_type(self) -> type:
        """Get the root dictionary's value type.

        This is determined by the annotation of the root field in the model.
        """
        value_type = get_args(self.__class__.model_fields["root"].annotation)[1]

        # If the value type is a string, it means it's a forward reference, and we can resolve it.
        if isinstance(value_type, str):
            value_type = ForwardRef(value_type)._evaluate(globals(), locals(), frozenset())  # noqa: SLF001

        if value_type is None:
            raise ValueError(f"Value type for {self.__name__} is None.")  # noqa: TRY003, EM102

        return value_type

    def __getitem__(self, item: K) -> V:
        """Get an item from the root dictionary, creating it if it doesn't exist."""
        if item not in self.root:
            # Create a new instance of the value type assign it to the dictionary.
            # The value type is expected to be initializable with no arguments.
            self.root[item] = self.value_type()

        return self.root[item]

    def __setitem__(self, key: K, value: V) -> None:
        """Set an item in the root dictionary."""
        self.root[key] = value

    def pop(self, key: K, default: D = None) -> V | D: # type: ignore[override]
        """Pop an item from the root dictionary."""
        return self.root.pop(key, default)

    def keys(self) -> KeysView[K]:
        """Get the keys of the root dictionary."""
        return self.root.keys()

    def values(self) -> ValuesView[V]:
        """Get the values of the root dictionary."""
        return self.root.values()

    def __iter__(self) -> Iterator[K]:  # type: ignore[override]
        """Iterate over the keys in the root dictionary."""
        return iter(self.root)

    def __delitem__(self, key: K) -> None:
        """Delete an item from the root dictionary."""
        del self.root[key]

    def __contains__(self, item: object) -> bool:
        """Check if an item is in the root dictionary."""
        return item in self.root

    def __len__(self) -> int:
        """Get the length of the root dictionary."""
        return len(self.root)


class PluginDataDictModel(RootDefaultDictModel[DeviceUUIDStr, "DeviceDataDictModel"]):
    """A model for holding the plugin state data.

    This model inherits from RootModel to provide a dictionary-like interface to the plugin state data.
    It uses a defaultdict-like approach to create new instances of the device data model
    when they are accessed for the first time.
    """

    model_config = ConfigDict(
        validate_assignment=True,
        # revalidate_instances="always",  # Probably not needed here.
    )

    def __init__(self) -> None:
        super().__init__(root={})


class DeviceDataDictModel(BaseModel):
    """A model for holding the device data.

    This model is used to store the device info and the action data for the device.
    """
    actions: ActionDataDictModel
    info: Optional[DeviceInfo] = None  # noqa: UP007

    def __init__(self, actions: ActionDataDictModel | None = None, info: DeviceInfo | None = None) -> None:
        super().__init__(actions=actions or {}, info=info)


class ActionDataDictModel(RootDefaultDictModel[ActionUUIDStr, "ActionInstanceMapModel"]):
    """A model for holding the action data.

    This model inherits from RootModel to provide a dictionary-like interface to the action data.
    It uses a defaultdict-like approach to create new instances of the action data model
    when they are accessed for the first time.
    """



class ActionInstanceMapModel(RootDefaultDictModel[ActionInstanceUUIDStr, "ActionInstanceDataDictModel"]):
    """A model for holding the action instance data.

    This model inherits from RootModel to provide a dictionary-like interface to the action instance data.
    It uses a defaultdict-like approach to create new instances of the action instance data model
    when they are accessed for the first time.
    """

    def __init__(self) -> None:
        super().__init__({})  # type: ignore[arg-type]


class ActionInstanceDataDictModel(BaseModel):
    """Model for holding the action instance data."""
    settings: PluginDefinedData
    coordinates: Optional[Coordinates] = None  # noqa: UP007

    def __init__(self, settings: PluginDefinedData | None = None, coordinates: CoordinatesDict | None = None) -> None:
        super().__init__(settings=settings or {}, coordinates=coordinates or None)


