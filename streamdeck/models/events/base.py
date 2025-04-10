from __future__ import annotations

from abc import ABC
from typing import Any, Generic, Literal, get_args, get_origin

from pydantic import BaseModel, ConfigDict
from pydantic._internal._generics import get_origin as get_model_origin
from typing_extensions import (  # noqa: UP035
    LiteralString,
    TypeGuard,
    TypeVar,
    override,
)


class ConfiguredBaseModel(BaseModel, ABC):
    """Base class for models that share the same configuration."""
    # Configure to use the docstrings of the fields as the field descriptions,
    # and to serialize the fields by their aliases.
    model_config = ConfigDict(use_attribute_docstrings=True, serialize_by_alias=True)

    @override
    def model_dump_json(self, **kwargs: Any) -> str:
        """Dump the model to JSON, excluding default values by default.

        Fields with default values in this context are those that are not required by the model,
        and are given a default value of None. Thus, for the serialized JSON to have parity with the
        StreamDeck-provided JSON event messages, we need to exclude fields not found in the event message.

        Unfortunately, the `exclude_defaults` option is not available in the ConfigDict configuration,
        nor in the Field parameters. To work around this, we wrap the `model_dump_json` method
        to set `exclude_defaults` to `True` by default.
        """
        kwargs.setdefault("exclude_defaults", True)
        return super().model_dump_json(**kwargs)


def is_literal_str_type(value: object | None) -> TypeGuard[LiteralString]:
    """Check if a type is a concrete Literal type with string args."""
    if value is None:
        return False

    if isinstance(value, TypeVar):
        return False

    event_field_base_type = get_origin(value)

    if event_field_base_type is not Literal:
        return False

    return all(isinstance(literal_value, str) for literal_value in get_args(value))


## EventBase implementation model of the Stream Deck Plugin SDK events.

EventName_co = TypeVar("EventName_co", bound=str, default=str, covariant=True)


class EventBase(ConfiguredBaseModel, ABC, Generic[EventName_co]):
    """Base class for event models that represent Stream Deck Plugin SDK events."""

    event: EventName_co
    """Name of the event used to identify what occurred.

    Subclass models must define this field as a Literal type with the event name string that the model represents.
    """

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Validate that the event field is a Literal[str] type."""
        super().__init_subclass__(**kwargs)

        # This is a GenericAlias (likely used in the subclass definition, i.e. `class ConcreteEvent(EventBase[Literal["event_name"]]):`) which is technically a subclass.
        # We can safely ignore this case, as we only want to validate the concrete subclass itself (`ConscreteEvent`).
        if get_model_origin(cls) is None:
            return

        model_event_type = cls.__event_type__()

        if not is_literal_str_type(model_event_type):
            msg = f"The event field annotation must be a Literal[str] type. Given type: {model_event_type}"
            raise TypeError(msg)

    @classmethod
    def __event_type__(cls) -> type[object]:
        """Get the type annotations of the subclass model's event field."""
        return cls.model_fields["event"].annotation  # type: ignore[index]

    @classmethod
    def get_model_event_names(cls) -> tuple[str, ...]:
        """Get the value of the subclass model's event field Literal annotation."""
        model_event_type = cls.__event_type__()

        # Ensure that the event field annotation is a Literal type.
        if not is_literal_str_type(model_event_type):
            msg = f"The event field annotation of an Event model must be a Literal[str] type. Given type: {model_event_type}"
            raise TypeError(msg)

        return get_args(model_event_type)
