"""Storage for objects that can be injected into event handler parameters."""

from __future__ import annotations

import inspect
from collections.abc import Callable, Iterable

from streamdeck.event_handlers.protocol import (
    EventHandlerFunc,
    EventModel_contra,
    inspect_event_handler_signature,
    validate_event_handler_event_parameter,
)


class InjectableHandlerParamStore:
    """Store injectable objects and resolve them by handler parameter name."""

    def __init__(self) -> None:
        self._values: dict[str, object] = {}

    @property
    def parameter_names(self) -> frozenset[str]:
        """Names of the objects currently held by the store."""
        return frozenset(self._values)

    def set_value(self, name: str, value: object) -> None:
        """Store a value under an injectable parameter name."""
        if name == "event_data":
            msg = "'event_data' is reserved for the required event parameter"
            raise ValueError(msg)

        self._values[name] = value

    def resolve(self, parameter_names: Iterable[str]) -> dict[str, object]:
        """Return stored values whose names are requested by a handler."""
        return {
            name: self._values[name]
            for name in parameter_names
            if name in self._values
        }

    def resolve_for_handler(self, handler: Callable[..., None]) -> dict[str, object]:
        """Return stored values only for parameters declared by a handler."""
        return self.resolve(inspect.signature(handler).parameters)

    def validate_handler_signature(self, handler: EventHandlerFunc[EventModel_contra, ...]) -> None:
        """Validate that the store can supply every required handler parameter after the event."""
        handler_signature = inspect_event_handler_signature(handler)
        validate_event_handler_event_parameter(handler_signature)
        injectable_parameters = {
            name: handler_signature.parameters[name]
            for name in self.parameter_names
            if name in handler_signature.parameters
        }
        for name, parameter in injectable_parameters.items():
            if parameter.kind not in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY):
                msg = f"Invalid event handler signature for {handler!r}: {name!r} must accept a keyword argument"
                raise TypeError(msg)

        # Check that dispatch can satisfy every required parameter without calling the handler.
        # Simulate dispatch's call shape: event_data positionally, plus stored values by keyword.
        # Binding fails if any required parameter is missing.
        bind_kwargs = {name: object() for name in injectable_parameters}
        try:
            handler_signature.bind(object(), **bind_kwargs)
        except TypeError as exc:
            msg = f"Invalid event handler signature for {handler!r}: {exc}"
            raise TypeError(msg) from exc
