"""Scopes used to limit which events can provide injectable parameters."""

from __future__ import annotations

from enum import Flag, auto
from typing import TYPE_CHECKING, Literal

from streamdeck.models.events.common import ContextualEventMixin, DeviceSpecificEventMixin


if TYPE_CHECKING:
    from collections.abc import Callable

    from streamdeck.models.events.base import EventBase


ScopeName = Literal["Plugin", "Device", "ActionInstance", "ActionInstanceWithDevice"]
"""A named injectable scope exposed in plugin configuration."""


class Scope(Flag):
    """Represent event identity capabilities used to check injectable availability.

    Flags can be combined when an event provides multiple identities. `PLUGIN` is
    zero because plugin-scoped injectables require no event identity.
    """

    PLUGIN = 0
    """No device or action-instance identity is required."""
    DEVICE = auto()
    """The event provides a device identity."""
    ACTION_INSTANCE = auto()
    """The event provides an action-instance identity."""

    ACTION_INSTANCE_WITH_DEVICE = DEVICE | ACTION_INSTANCE
    """The event provides both device and action-instance identities."""


SCOPE_CAPABILITIES: dict[ScopeName, Scope] = {
    "Plugin": Scope.PLUGIN,
    "Device": Scope.DEVICE,
    "ActionInstance": Scope.ACTION_INSTANCE,
    "ActionInstanceWithDevice": Scope.ACTION_INSTANCE_WITH_DEVICE,
}
"""Map each configured scope name to the identities it requires."""


def scope_covers(required_scope: ScopeName, event_scope: Scope) -> bool:
    """Return whether an event scope provides the identities required by an injectable.

    Args:
        required_scope: The minimum scope required by the injectable parameter.
        event_scope: The identity scope available on the event.

    Returns:
        Whether the event provides every identity required by the injectable.
    """
    required = SCOPE_CAPABILITIES[required_scope]
    return required & event_scope == required


def scope_for_event(event_or_model: EventBase | type[EventBase]) -> Scope:
    """Return the identity capabilities available on an event or its model.

    Args:
        event_or_model: A validated event instance or its event model class.

    Returns:
        The combined device and action-instance identities provided by the event.
    """
    # Params default to Plugin scope (no filtering is applied)
    scope = Scope.PLUGIN

    scope_check: Callable[..., bool] = (
        issubclass if isinstance(event_or_model, type) else isinstance
    )

    if scope_check(event_or_model, ContextualEventMixin):
        scope |= Scope.ACTION_INSTANCE
    if scope_check(event_or_model, DeviceSpecificEventMixin):
        scope |= Scope.DEVICE

    return scope
