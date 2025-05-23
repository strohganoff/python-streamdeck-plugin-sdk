from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from typing import Any, Literal

    from streamdeck.types import (
        ActionInstanceUUIDStr,
        ActionUUIDStr,
        DeviceUUIDStr,
        EventNameStr,
        PluginDefinedData,
    )
    from streamdeck.websocket import WebSocketClient



logger = getLogger("streamdeck.command_sender")


class StreamDeckCommandSender:
    """Class for sending command event messages to the Stream Deck software through a WebSocket client."""

    def __init__(self, client: WebSocketClient, plugin_registration_uuid: str):
        self._client = client
        self._plugin_registration_uuid = plugin_registration_uuid

    def _send_event(self, event: EventNameStr, **kwargs: Any) -> None:
        self._client.send_event({
            "event": event,
            **kwargs,
        })

    def set_settings(self, context: ActionInstanceUUIDStr, payload: PluginDefinedData) -> None:
        self._send_event(
            event="setSettings",
            context=context,
            payload=payload,
        )

    def get_settings(self, context: ActionInstanceUUIDStr) -> None:
        self._send_event(
            event="getSettings",
            context=context,
        )

    def set_global_settings(self, payload: PluginDefinedData) -> None:
        self._send_event(
            event="setGlobalSettings",
            context=self._plugin_registration_uuid,
            payload=payload,
        )

    def get_global_settings(self) -> None:
        self._send_event(
            event="getGlobalSettings",
            context=self._plugin_registration_uuid,
        )

    def open_url(self, context: ActionInstanceUUIDStr, url: str) -> None:
        self._send_event(
            event="openUrl",
            context=context,
            payload={"url": url},
        )

    def log_message(self, context: ActionInstanceUUIDStr, message: str) -> None:
        self._send_event(
            event="logMessage",
            context=context,
            payload={"message": message},
        )

    def set_title(
        self,
        context: ActionInstanceUUIDStr,
        state: int | None = None,
        target: Literal["hardware", "software", "both"] | None = None,
        title: str | None = None,
    ) -> None:
        payload = {}

        if state is not None:
            payload["state"] = state
        if target:
            payload["target"] = target
        if title:
            payload["title"] = title

        self._send_event(
            event="setTitle",
            context=context,
            payload=payload,
        )

    def set_image(
        self,
        context: ActionInstanceUUIDStr,
        image: str,  # base64 encoded image,
        target: Literal["hardware", "software", "both"],
        state: int,
    ) -> None:
        """...

        Raises:
            KeyError: Raised when user passes in an invalid `target` value.
        """
        target_code_lookup = {
            "hardware": 1,
            "software": 2,
            "both": 0,
        }
        target_code = target_code_lookup[target]

        self._send_event(
            event="setImage",
            context=context,
            payload={
                "image": image,
                "target": target_code,
                "state": state,
            },
        )

    def set_feedback(self, context: ActionInstanceUUIDStr, payload: PluginDefinedData) -> None:
        """Set's the feedback of an existing layout associated with an action instance.

        Args:
          context (str): Defines the context of the command, e.g. which action instance the command is intended for.
          payload (PluginDefinedData): Additional information supplied as part of the command.
        """
        self._send_event(
            event="setFeedback",
            context=context,
            payload=payload,
        )

    def set_feedback_layout(self, context: ActionInstanceUUIDStr, layout: str) -> None:
        """Sets the layout associated with an action instance.

        Args:
          context (str): Defines the context of the command, e.g. which action instance the command is intended for.
          layout (str): Name of a pre-defined layout, or relative path to a custom one.
        """
        self._send_event(
            event="setFeedbackLayout",
            context=context,
            payload={"layout": layout},
        )

    def set_trigger_description(
        self,
        context: ActionInstanceUUIDStr,
        rotate: str | None = None,
        push: str | None = None,
        touch: str | None = None,
        long_touch: str | None = None,
    ) -> None:
        """Sets the trigger descriptions associated with an encoder (touch display + dial) action instance.

        All descriptions args (rotate, push, touch, and long_touch) are optional;
        when one or more descriptions are defined all descriptions are updated,
        with undefined values having their description hidden in Stream Deck.

        To reset the descriptions to the default values defined within the manifest,
        an empty payload can be sent as part of the event.

        Args:
            context: ...
            rotate: Describes the rotate interaction with the dial.
                When None, the description will be hidden.
            push: Describes the push interaction with the dial.
                When None, the description will be hidden.
            touch: Describes the touch interaction with the touch display.
                When None, the description will be hidden
            long_touch: Describes the long-touch interaction with the touch display.
                When None, the description will be hidden.
        """
        self._send_event(
            event="setTriggerDescription",
            context=context,
            payload={
                "rotate": rotate or "undefined",
                "push": push or "undefined",
                "touch": touch or "undefined",
                "longTouch": long_touch or "undefined",
            },
        )

    def show_alert(self, context: ActionInstanceUUIDStr) -> None:
        """Temporarily show an alert icon on the image displayed by an instance of an action."""
        self._send_event(
            event="showAlert",
            context=context,
        )

    def show_ok(self, context: ActionInstanceUUIDStr) -> None:
        """Temporarily show an OK checkmark icon on the image displayed by an instance of an action."""
        self._send_event(
            event="showOk",
            context=context,
        )

    def set_state(self, context: ActionInstanceUUIDStr, state: int) -> None:
        self._send_event(
            event="setState",
            context=context,
            payload={"state": state},
        )

    def switch_to_profile(
        self,
        context: ActionInstanceUUIDStr,
        device: DeviceUUIDStr,
        profile: str | None = None,
        page: int = 0,
    ) -> None:
        """Switch to one of the preconfigured read-only profiles.

        NOTE: a plugin can only switch to read-only profiles declared in its manifest.json file.
            If the profile field is missing or empty, the Stream Deck application will switch to
            the previously selected profile.

        Args:
            device (str): A unique value to identify the device.  # TODO: What device? The one pressing the button?
            profile (str): The name of the profile to switch to.
                The name should be identical to the name provided in the manifest.json file.
            page (int):  Page to show when switching to the profile; indexed from 0.
        """
        # TODO: Should validation happen that ensures the specified profile is declared in manifest.yaml?
        payload: dict[str, str | int | None] = {}

        if profile is not None:
            payload = {
                "profile": profile,
                "page": page,
            }

        self._send_event(
            event="switchToProfile",
            context=context,
            device=device,
            payload=payload,
        )

    def send_to_property_inspector(
        self, context: ActionInstanceUUIDStr, payload: PluginDefinedData
    ) -> None:
        self._send_event(
            event="sendToPropertyInspector",
            context=context,
            payload=payload,
        )

    def send_to_plugin(
        self, context: ActionInstanceUUIDStr, action: ActionUUIDStr, payload: PluginDefinedData
    ) -> None:
        """Send a payload to another plugin.

        Args:
            action: The unique identifier of the receiving plugin's action.
                If your plugin supports multiple actions, you should use this value to find out
                which action was triggered.
            payload: The data that will be received by the receiving plugin.
        """
        self._send_event(
            event="sendToPlugin",
            context=context,
            action=action,
            payload=payload,
        )

    def send_action_registration(
        self,
        register_event: str,
    ) -> None:
        """Registers a plugin with the Stream Deck software very shortly after the plugin is started.

        Upon running a plugin's startup command, the Stream Deck software will pass in args that include a
        register event type string (almost definitely "registerPlugin") and a unique random ID, which the
        plugin needs to immediately send back as an event message in order to register itself.
        If the Stream Deck software doesn't receive this event after a very brief period, it will keep
        trying to re-run the plugin until getting the event.

        Args:
            register_event (str): The registration event type, passed in by the Stream Deck software as -registerEvent option.
                It's value will almost definitely will be "registerPlugin".
        """
        self._send_event(
            event=register_event,
            uuid=self._plugin_registration_uuid,
        )
