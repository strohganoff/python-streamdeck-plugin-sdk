"""Context objects built from Stream Deck startup arguments and events."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import singledispatchmethod
from typing import TYPE_CHECKING, Protocol

from streamdeck.event_handlers.actions import GlobalAction
from streamdeck.models.events import DEFAULT_EVENT_MODELS
from streamdeck.models.events.common import (
    BasePayload,
    ContextualEventMixin,
    ContextualPayloadEventMixin,
    ControllerType,
    Coordinates,
    CoordinatesPayloadMixin,
    DeviceSpecificEventMixin,
    SettingsPayloadMixin,
    StatefulActionPayloadMixin,
)
from streamdeck.models.events.devices import DeviceDidConnect, DeviceDidDisconnect, DeviceInfo
from streamdeck.models.events.property_inspector import DidReceivePropertyInspectorMessage
from streamdeck.models.events.settings import DidReceiveGlobalSettings


if TYPE_CHECKING:
    from streamdeck.event_handlers.injectables import InjectableResolver
    from streamdeck.event_handlers.scopes import ScopeName
    from streamdeck.models.events.base import EventBase
    from streamdeck.models.launch import RegistrationInfo
    from streamdeck.types import PluginDefinedData


class _InjectableHandlerParamRegistrar(Protocol):
    """Registration callable accepted by the context injectable setup helper."""

    def __call__(
        self,
        name: str,
        resolver: InjectableResolver[object],
        *,
        scope: ScopeName | None = None,
    ) -> None:
        """Register a resolver under a handler parameter name and scope."""
        ...


@dataclass(slots=True)
class PluginContext:
    """Plugin identity, startup metadata, and global settings."""

    plugin_uuid: str
    """UUID configured for the plugin in its manifest."""
    plugin_registration_uuid: str
    """Per-launch UUID supplied by Stream Deck for plugin registration."""
    info: PluginDefinedData
    """Plugin information passed in the launch arguments."""
    global_settings: PluginDefinedData = field(default_factory=dict)
    """Most recently received global plugin settings."""


@dataclass(slots=True)
class DeviceContext:
    """Information and connection status for one Stream Deck device."""

    device_id: str
    """Device identifier supplied by Stream Deck events."""
    info: DeviceInfo | None = None
    """Device details from the most recent deviceDidConnect event."""
    connected: bool | None = None
    """Whether Stream Deck has reported this device as connected."""


@dataclass(slots=True)
class ActionContext:
    """Identity shared by all instances of one registered action."""

    action_uuid: str
    """Action UUID supplied by Stream Deck events."""


@dataclass(slots=True)
class ActionInstanceContext:
    """Latest known settings and placement data for one action instance."""

    context_id: str
    """Context identifier supplied by Stream Deck events."""
    action: ActionContext
    """Action that owns this instance."""
    device: DeviceContext | None = None
    """Associated device when an event identifies one."""
    settings: PluginDefinedData = field(default_factory=dict)
    """Most recently received settings for this action instance."""
    state: int | None = None
    """Most recently reported state, when the action has multiple states."""
    controller: ControllerType | None = None
    """Most recently reported controller type."""
    coordinates: Coordinates | None = None
    """Most recently reported key or dial coordinates."""


class ContextStore:
    """Cache plugin, device, action, and action-instance contexts."""

    def __init__(
        self,
        plugin_registration_uuid: str,
        info: RegistrationInfo,
    ) -> None:
        """Initialize the context cache with plugin startup metadata.

        Args:
            plugin_registration_uuid: Per-launch registration UUID supplied by Stream Deck.
            info: Validated registration information from the startup arguments.
        """
        self.plugin = PluginContext(
            plugin_uuid=info.plugin_uuid,
            plugin_registration_uuid=plugin_registration_uuid,
            info=info.model_dump(),
        )
        self.devices: dict[str, DeviceContext] = {}
        self.actions: dict[str, ActionContext] = {}
        self.action_instances: dict[str, ActionInstanceContext] = {}

    @singledispatchmethod
    def update_from_event(self, event_data: EventBase) -> None:  # noqa: ARG002
        """Ignore event models that do not update a context.

        Registered implementations update global settings, device data, or action-instance
        data according to the concrete event model.

        Args:
            event_data: Validated event received from Stream Deck.
        """
        return

    @update_from_event.register
    def _update_global_settings(self, event_data: DidReceiveGlobalSettings) -> None:
        """Replace cached plugin settings with settings received from Stream Deck.

        Args:
            event_data: Event containing the latest global plugin settings.
        """
        self.plugin.global_settings = event_data.payload.settings

    @update_from_event.register
    def _update_device_connected(self, event_data: DeviceDidConnect) -> None:
        """Record device information and mark the device as connected.

        Args:
            event_data: Event identifying the connected device and its information.
        """
        device = self.get_device_context(event_data.device)
        device.info = event_data.device_info
        device.connected = True

    @update_from_event.register
    def _update_device_disconnected(self, event_data: DeviceDidDisconnect) -> None:
        """Mark the identified device as disconnected.

        Args:
            event_data: Event identifying the disconnected device.
        """
        self.get_device_context(event_data.device).connected = False

    @update_from_event.register
    def _update_contextual_event(self, event_data: ContextualEventMixin) -> None:
        """Update action-instance identity for a contextual event.

        Args:
            event_data: Event identifying an action and one of its instances.
        """
        self._get_or_create_action_instance_context(event_data)

    @update_from_event.register
    def _update_contextual_payload_event(
        self,
        event_data: ContextualPayloadEventMixin,
    ) -> None:
        """Update action-instance context values from a contextual event payload.

        Args:
            event_data: Contextual event with payload data that may update the context.
        """
        instance = self._get_or_create_action_instance_context(event_data)
        payload = event_data.payload

        # SettingsPayloadMixin is used by didReceiveSettings, keyDown/keyUp, willAppear/
        # willDisappear, dialDown/dialRotate/dialUp, titleParametersDidChange, and touchTap.
        if isinstance(payload, SettingsPayloadMixin):
            instance.settings = payload.settings

        # BasePayload subclasses on those events also carry controller information.
        if isinstance(payload, BasePayload) and payload.controller is not None:
            instance.controller = payload.controller

        # Stateful payloads are used by keyDown/keyUp, didReceiveSettings, willAppear/
        # willDisappear, and titleParametersDidChange.
        if isinstance(payload, StatefulActionPayloadMixin) and payload.state is not None:
            instance.state = payload.state

        # Coordinates occur on single-action didReceiveSettings, keyDown/keyUp, and
        # willAppear/willDisappear payloads, plus dialDown/dialRotate/dialUp,
        # titleParametersDidChange, and touchTap payloads.
        if isinstance(payload, CoordinatesPayloadMixin):
            instance.coordinates = payload.coordinates

    def get_device_context(self, device_id: str) -> DeviceContext:
        """Get a device context, creating a placeholder if it is not cached.

        Args:
            device_id: Stream Deck identifier for the device.

        Returns:
            The cached context for the requested device.
        """
        if device_id not in self.devices:
            self.devices[device_id] = DeviceContext(device_id=device_id)
        return self.devices[device_id]

    def get_action_context(self, action_uuid: str) -> ActionContext:
        """Get an action context, creating it if it is not cached.

        Args:
            action_uuid: UUID identifying the action.

        Returns:
            The cached context for the requested action.
        """
        if action_uuid not in self.actions:
            self.actions[action_uuid] = ActionContext(action_uuid=action_uuid)
        return self.actions[action_uuid]

    def _get_or_create_action_instance_context(
        self,
        event_data: ContextualEventMixin,
    ) -> ActionInstanceContext:
        """Get or create an action-instance context using event identity fields.

        Args:
            event_data: Event identifying the action instance and, when present, its device.

        Returns:
            The cached context for the identified action instance.
        """
        action = self.get_action_context(event_data.action)
        device = (
            self.get_device_context(event_data.device)
            if isinstance(event_data, DeviceSpecificEventMixin)
            else None
        )
        instance = self.action_instances.get(event_data.context)
        if instance is None:
            instance = ActionInstanceContext(
                context_id=event_data.context,
                action=action,
                device=device,
            )
            self.action_instances[event_data.context] = instance
        else:
            instance.action = action
            if device is not None:
                instance.device = device
        return instance

    def resolve_device_context(self, event_data: EventBase) -> DeviceContext:
        """Resolve the device context identified by a device-specific event.

        Args:
            event_data: Event expected to identify a device.

        Returns:
            The cached context for the event's device.

        Raises:
            TypeError: If the event does not identify a device.
        """
        if not isinstance(event_data, DeviceSpecificEventMixin):
            msg = f"Event {event_data.event!r} does not identify a device"
            raise TypeError(msg)
        return self.get_device_context(event_data.device)

    def resolve_action_context(self, event_data: EventBase) -> ActionContext:
        """Resolve the action context identified by a contextual event.

        Args:
            event_data: Event expected to identify an action.

        Returns:
            The cached context for the event's action.

        Raises:
            TypeError: If the event does not identify an action.
        """
        if not isinstance(event_data, ContextualEventMixin):
            msg = f"Event {event_data.event!r} does not identify an action"
            raise TypeError(msg)
        return self.get_action_context(event_data.action)

    def resolve_action_instance_context(self, event_data: EventBase) -> ActionInstanceContext:
        """Resolve the action-instance context identified by a contextual event.

        Args:
            event_data: Event expected to identify an action instance.

        Returns:
            The cached context for the event's action instance.

        Raises:
            TypeError: If the event does not identify an action instance.
        """
        if not isinstance(event_data, ContextualEventMixin):
            msg = f"Event {event_data.event!r} does not identify an action instance"
            raise TypeError(msg)

        return self._get_or_create_action_instance_context(event_data)


def register_context_handlers(context_store: ContextStore) -> GlobalAction:
    """Register context updates for relevant default Stream Deck event models.

    Args:
        context_store: Store updated by the internal event handlers.

    Returns:
        A global action containing the internal context update handlers.
    """
    context_actions = GlobalAction()

    for event_model in DEFAULT_EVENT_MODELS:
        # Skip sendToPlugin: its arbitrary payload is the only contextual event payload not used
        # to update cached context values.
        if event_model is DidReceivePropertyInspectorMessage:
            continue

        # Only register events that identify an action instance, a device, or global settings.
        if not issubclass(
            event_model,
            (ContextualEventMixin, DeviceSpecificEventMixin, DidReceiveGlobalSettings),
        ):
            continue

        for event_name in event_model.get_model_event_names():
            context_actions.on(event_name)(context_store.update_from_event)

    return context_actions


def register_context_injectables(
    context_store: ContextStore,
    register_injectable: _InjectableHandlerParamRegistrar,
) -> None:
    """Register built-in context resolvers with their event identity scopes.

    Args:
        context_store: Store that resolves the context objects.
        register_injectable: Registration callable for the built-in injectable resolvers.
    """
    register_injectable(
        "plugin_context",
        lambda _event_data: context_store.plugin,
        scope="Plugin",
    )
    register_injectable(
        "device_context", context_store.resolve_device_context, scope="Device"
    )
    register_injectable(
        "action_context",
        context_store.resolve_action_context,
        scope="ActionInstance",
    )
    register_injectable(
        "action_instance_context",
        context_store.resolve_action_instance_context,
        scope="ActionInstance",
    )
