from __future__ import annotations


## Mixin classes for common event model fields.

class ContextualEventMixin:
    """Mixin class for event models that have action and context fields."""
    action: str
    """Unique identifier of the action"""
    context: str
    """Identifies the instance of an action that caused the event, i.e. the specific key or dial."""


class DeviceSpecificEventMixin:
    """Mixin class for event models that have a device field."""
    device: str
    """Unique identifier of the Stream Deck device that this event is associated with."""
