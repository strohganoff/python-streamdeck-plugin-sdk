from polyfactory.factories.pydantic_factory import ModelFactory
from streamdeck.models import events


class DialDownEventFactory(ModelFactory[events.DialDown]):
    """Polyfactory factory for creating a fake dialDown event message based on our Pydantic model."""


class DialUpEventFactory(ModelFactory[events.DialUp]):
    """Polyfactory factory for creating a fake dialUp event message based on our Pydantic model."""


class DialRotateEventFactory(ModelFactory[events.DialRotate]):
    """Polyfactory factory for creating a fake event message based on our Pydantic model."""


class KeyDownEventFactory(ModelFactory[events.KeyDown]):
    """Polyfactory factory for creating fake keyDown event message based on our Pydantic model.

    KeyDownEvent's have the unique identifier properties:
        `device`: Identifies the Stream Deck device that this event is associated with.
        `action`: Identifies the action that caused the event.
        `context`: Identifies the *instance* of an action that caused the event.
    """


class KeyUpEventFactory(ModelFactory[events.KeyUp]):
    """Polyfactory factory for creating a fake keyUp event message based on our Pydantic model."""


class ApplicationDidLaunchEventFactory(ModelFactory[events.ApplicationDidLaunch]):
    """Polyfactory factory for creating fake applicationDidLaunch event message based on our Pydantic model.

    ApplicationDidLaunchEvent's hold no unique identifier properties, besides the almost irrelevant `event` name property.
    """


class DeviceDidConnectFactory(ModelFactory[events.DeviceDidConnect]):
    """Polyfactory factory for creating fake deviceDidConnect event message based on our Pydantic model.

    DeviceDidConnectEvent's have `device` unique identifier property.
    """
