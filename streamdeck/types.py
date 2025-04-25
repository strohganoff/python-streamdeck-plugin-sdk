# ruff: noqa: UP040
from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import JsonValue


if TYPE_CHECKING:
    from typing_extensions import TypeAlias  # noqa: UP035



EventNameStr: TypeAlias = str
"""Type alias for the event name string.

We don't define literal string values here, as the list of available event names can be added to dynamically.
"""

DeviceUUIDStr: TypeAlias = str
"""Unique identifier string of a Stream Deck device that an event is associated with."""

ActionUUIDStr: TypeAlias = str
"""Unique identifier string of a Stream Deck action that an event is associated with."""

ActionInstanceUUIDStr: TypeAlias = str
"""Unique identifier string of a specific instance of an action that an event is associated with (e.g. a specific key or dial that the action is assigned to)."""

PluginDefinedData: TypeAlias = dict[str, JsonValue]
"""Key-value pair data of arbitrary structure that is defined in and relevant to the plugin.

The root of the data structure will always be a dict of string keys, while the values can be any JSON-compatible type.
"""
