from __future__ import annotations

import pytest
from streamdeck.models.events import (
    DeviceDidConnect,
    DeviceDidDisconnect,
    DidReceiveSettings,
    WillAppear,
)
from streamdeck.models.events.common import Coordinates
from streamdeck.state import PluginDataDictModel, PluginState

from tests.test_utils.fake_event_factories import (
    DeviceDidConnectFactory,
    DeviceDidDisconnectFactory,
    DidReceiveSettingsFactory,
    WillAppearFactory,
)


def test_init():
    """Test that PluginState initializes with an empty PluginDataDictModel."""
    state = PluginState()
    assert isinstance(state.data, PluginDataDictModel)
    assert state.data.model_dump() == {}


def test_set_initial_state():
    """Test that set_initial_state properly updates the state from WillAppear event."""
    # Reset singleton state for clean test
    PluginState._instance = None
    state = PluginState()

    event = WillAppearFactory.build(
        device="device1",
        action="action1",
        context="context1",
        payload={
            "controller": "Keypad",
            "isInMultiAction": False,
            "settings": {"key": "value"},
            "coordinates": {"column": 0, "row": 0},
        },
    )

    state.set_initial_state(event)

    # Verify data was stored correctly
    assert state.data["device1"].actions["action1"]["context1"].settings == {"key": "value"}
    assert state.data["device1"].actions["action1"]["context1"].coordinates == Coordinates(column=0, row=0)


def test_update_instance_settings():
    """Test that update_instance_settings properly updates settings from DidReceiveSettings event."""
    # Reset singleton state for clean test
    PluginState._instance = None
    state = PluginState()

    # First set initial state
    initial_event: WillAppear = WillAppearFactory.build(
        device="device1",
        action="action1",
        context="context1",
        payload={
            "controller": "Keypad",
            "isInMultiAction": False,
            "settings": {"key": "initial"},
            "coordinates": {"column": 0, "row": 0},
        },
    )
    state.set_initial_state(initial_event)

    # Then update it
    update_event: DidReceiveSettings = DidReceiveSettingsFactory.build(
        device="device1",
        action="action1",
        context="context1",
        payload={
            "controller": "Keypad",
            "isInMultiAction": False,
            "settings": {"key": "updated"},
            "coordinates": {"column": 0, "row": 0},
        },
    )
    state.update_instance_settings(update_event)

    # Verify data was updated correctly
    assert state.data["device1"].actions["action1"]["context1"].settings == {"key": "updated"}
    assert state.data["device1"].actions["action1"]["context1"].coordinates == Coordinates(column=0, row=0)


def test_access_nonexistent_data():
    """Test that accessing nonexistent data entries creates the required structure."""
    # Reset singleton state for clean test
    PluginState._instance = None
    state = PluginState()

    # Access data that doesn't exist yet
    settings = state.data["new_device"].actions["new_action"]["new_context"].settings

    # Verify the structure was created
    assert isinstance(settings, dict)
    assert settings == {}
    assert "new_device" in state.data.root
    assert "new_action" in state.data["new_device"].actions.root
    assert "new_context" in state.data["new_device"].actions["new_action"].root


def test_multiple_instances():
    """Test that multiple action instances can be stored."""
    # Reset singleton state for clean test
    PluginState._instance = None
    state = PluginState()

    # Add multiple instances
    for i in range(3):
        event: WillAppear = WillAppearFactory.build(
            device="device1",
            action="action1",
            context=f"context{i}",
            payload={
                "controller": "Keypad",
                "isInMultiAction": False,
                "settings": {"instance": i},
                "coordinates": {"column": i, "row": i},
            },
        )
        state.set_initial_state(event)

    # Verify all instances are stored correctly
    for i in range(3):
        assert state.data["device1"].actions["action1"][f"context{i}"].settings == {"instance": i}
        assert state.data["device1"].actions["action1"][f"context{i}"].coordinates == Coordinates(column=i, row=i)


def test_without_coordinates():
    """Test event handling when coordinates are not provided."""
    # Reset singleton state for clean test
    PluginState._instance = None
    state = PluginState()

    # Create event without coordinates—MultiAction event payloads don't have coordinates.
    multi_event: WillAppear = WillAppear.model_validate({
        "event": "willAppear",
        "device": "device1",
        "action": "action1",
        "context": "context1",
        "payload": {
            "controller": "Keypad",
            "isInMultiAction": True,
            "settings": {"key": "value"},
        },
    })

    # This should not raise an error
    state.set_initial_state(multi_event)

    # Verify settings were stored but coordinates remain None
    assert state.data["device1"].actions["action1"]["context1"].settings == {"key": "value"}
    assert state.data["device1"].actions["action1"]["context1"].coordinates is None


def test_add_device():
    """Test that a deviceDidConnect event adds a new device to the plugin state."""
    # Reset singleton state for clean test
    PluginState._instance = None
    plugin_state = PluginState()

    event: DeviceDidConnect = DeviceDidConnectFactory.build(
        device="device3",
    )
    # Stash the device info for later use
    device_info = event.device_info

    plugin_state.add_device(event)

    # Verify the device was added
    assert "device3" in plugin_state.data
    assert plugin_state.data["device3"].info is not None
    assert plugin_state.data["device3"].info == device_info


def test_delete_device():
    """Test that a deviceDidDisconnect event removes the device and related data from the plugin state."""
    PluginState._instance = None
    state = PluginState()

    # Add some data
    event: WillAppear = WillAppearFactory.build(
        device="device4",
        action="action1",
        context="context1",
        payload={
            "controller": "Keypad",
            "isInMultiAction": False,
            "settings": {"key": "value"},
            "coordinates": {"column": 0, "row": 0},
        },
    )
    state.set_initial_state(event)

    event2: DeviceDidDisconnect = DeviceDidDisconnectFactory.build(
        device="device4",
    )
    state.remove_data_for_device(event2)

    # Verify the device and its data were removed
    assert "device4" not in state.data.root
    assert "context1" not in state.action_instances
