from __future__ import annotations

from abc import ABC
from typing import Any, Literal, get_args, get_type_hints

from pydantic import BaseModel, ConfigDict
from typing_extensions import LiteralString, TypeIs  # noqa: UP035


def is_literal_str_type(value: object | None) -> TypeIs[LiteralString]:
    """Check if a type is a Literal type with string values."""
    if value is None:
        return False

    event_field_base_type = getattr(value, "__origin__", None)

    if event_field_base_type is not Literal:
        return False

    return all(isinstance(literal_value, str) for literal_value in get_args(value))


## EventBase implementation models of the Stream Deck Plugin SDK events.

class EventBase(BaseModel, ABC):
    """Base class for event models that represent Stream Deck Plugin SDK events."""
    # Configure to use the docstrings of the fields as the field descriptions.
    model_config = ConfigDict(use_attribute_docstrings=True)

    event: str
    """Name of the event used to identify what occurred.

    Subclass models must define this field as a Literal type with the event name string that the model represents.
    """

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Validate that the event field is a Literal[str] type."""
        super().__init_subclass__(**kwargs)

        model_event_type = cls.get_event_type_annotations()

        if not is_literal_str_type(model_event_type):
            msg = f"The event field annotation must be a Literal[str] type. Given type: {model_event_type}"
            raise TypeError(msg)

    @classmethod
    def get_event_type_annotations(cls) -> type[object]:
        """Get the type annotations of the subclass model's event field."""
        return get_type_hints(cls)["event"]

    @classmethod
    def get_model_event_name(cls) -> tuple[str, ...]:
        """Get the value of the subclass model's event field Literal annotation."""
        model_event_type = cls.get_event_type_annotations()

        # Ensure that the event field annotation is a Literal type.
        if not is_literal_str_type(model_event_type):
            msg = "The `event` field annotation of an Event model must be a Literal[str] type."
            raise TypeError(msg)

        return get_args(model_event_type)
