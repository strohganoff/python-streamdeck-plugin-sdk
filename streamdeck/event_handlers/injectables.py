"""Storage for objects that can be injected into event handler parameters."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, Protocol, TypeVar

from streamdeck.event_handlers.protocol import (
    EventHandlerFunc,
    EventModel_contra,
    inspect_event_handler_signature,
    validate_event_handler_event_parameter,
)
from streamdeck.event_handlers.scopes import Scope, ScopeName, scope_covers


if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from streamdeck.models.events.base import EventBase


# Resolvers and specs only expose their value as a return type, so this can be covariant.
Value_co = TypeVar("Value_co", covariant=True)
"""Covariant injectable value returned by a resolver."""


# `register` accepts a resolver, so its method-level type variable must remain invariant.
Value = TypeVar("Value")
"""Injectable value type inferred when registering a resolver."""


class InjectableResolver(Protocol[Value_co]):
    """Resolve an injectable value using the event being handled."""

    def __call__(self, event_data: EventBase, /) -> Value_co:
        """Return the injectable value for an event."""
        ...


@dataclass(frozen=True)
class InjectableSpec(Generic[Value_co]):
    """Resolver and availability scope for an injectable handler parameter."""

    scope: ScopeName
    """Narrowest event scope where this injectable is available."""

    resolve: InjectableResolver[Value_co]
    """Resolve the injectable value for the event being handled."""


class InjectableHandlerParamStore:
    """Store event-aware injectable resolvers and resolve them by handler parameter name."""

    def __init__(self) -> None:
        """Initialize an empty injectable resolver store."""
        self._specs: dict[str, InjectableSpec[object]] = {}
        self._scopes: dict[str, ScopeName] = {}

    @property
    def parameter_names(self) -> frozenset[str]:
        """Names of the injectable resolvers currently held by the store."""
        return frozenset(self._specs)

    def register_scope(self, name: str, scope: ScopeName) -> None:
        """Set the availability scope for an injectable handler parameter."""
        if name == "event_data":
            msg = "'event_data' is reserved for the required event parameter"
            raise ValueError(msg)

        self._scopes[name] = scope
        if name in self._specs:
            spec = self._specs[name]
            self._specs[name] = InjectableSpec(scope=scope, resolve=spec.resolve)

    def register(
        self,
        name: str,
        resolver: InjectableResolver[Value],
        *,
        scope: ScopeName | None = None,
    ) -> None:
        """Register a resolver under an injectable parameter name."""
        if name == "event_data":
            msg = "'event_data' is reserved for the required event parameter"
            raise ValueError(msg)

        spec: InjectableSpec[Value] = InjectableSpec(
            scope=scope if scope is not None else self._scopes.get(name, "Plugin"),
            resolve=resolver,
        )
        self._specs[name] = spec

    def resolve(self, parameter_names: Iterable[str], event_data: EventBase) -> dict[str, object]:
        """Resolve named injectables for the event being handled."""
        return {
            name: self._specs[name].resolve(event_data)
            for name in parameter_names
            if name in self._specs
        }

    def resolve_for_handler(self, handler: Callable[..., None], event_data: EventBase) -> dict[str, object]:
        """Resolve values only for injectable parameters declared by a handler."""
        return self.resolve(inspect.signature(handler).parameters, event_data)

    def validate_handler_signature(
        self,
        handler: EventHandlerFunc[EventModel_contra, ...],
        event_scopes: Iterable[Scope],
        event_name: str,
    ) -> None:
        """Validate handler binding and injectable scopes for one subscribed event."""
        handler_signature = inspect_event_handler_signature(handler)
        validate_event_handler_event_parameter(handler_signature)
        event_scopes = tuple(event_scopes)
        injectable_parameters = {
            name: handler_signature.parameters[name]
            for name in self._specs
            if name in handler_signature.parameters
        }
        for name, parameter in injectable_parameters.items():
            if parameter.kind not in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY):
                msg = f"Invalid event handler signature for {handler!r}: {name!r} must accept a keyword argument"
                raise TypeError(msg)

            spec = self._specs[name]
            if any(not scope_covers(spec.scope, event_scope) for event_scope in event_scopes):
                msg = (
                    f"Invalid event handler signature for {handler!r}: injectable parameter {name!r} "
                    f"requires {spec.scope!r} scope, which is not available for event {event_name!r}"
                )
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
