"""Shared Pydantic base classes for incoming event models."""

from __future__ import annotations

from abc import ABC
from typing import Annotated, Any, ClassVar, Generic, Literal, get_args, get_origin

from pydantic import BaseModel, ConfigDict, GetPydanticSchema
from typing_extensions import LiteralString, TypeAlias, TypeVar, override


StringLiteralType: TypeAlias = Annotated[
    LiteralString,
    GetPydanticSchema(lambda _source_type, handler: handler(str)),
]
"""A string-valued Literal type, with a Pydantic schema fallback to str."""

EventNameT = TypeVar("EventNameT", bound=StringLiteralType, default=Any)


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


class EventBase(ConfiguredBaseModel, Generic[EventNameT]):
    """Base class for all event models.

    EventBase itself and its generic specializations should not be instantiated.
    Define concrete event models by specializing with a string-valued Literal,
    for example `class KeyDown(EventBase[Literal["keyDown"]]): ...`.
    """

    event: EventNameT
    """Name of the event used to identify what occurred."""

    __event_names__: ClassVar[tuple[str, ...]] = ()
    """The event names declared by the generic EventBase specialization."""

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:  # noqa: ANN401
        """Validate EventBase generic arguments and require a specialization on subclasses."""
        super().__pydantic_init_subclass__(**kwargs)

        if cls is EventBase:
            return

        metadata = cls.__pydantic_generic_metadata__
        if metadata.get("origin") is EventBase:
            args = metadata["args"]
            if len(args) != 1 or get_origin(args[0]) is not Literal:
                msg = "EventBase must be specialized with Literal[str, ...]"
                raise TypeError(msg)

            names = get_args(args[0])
            if not names or any(type(name) is not str for name in names):
                msg = "EventBase Literal arguments must be strings"
                raise TypeError(msg)

            cls.__event_names__ = names
            return

        if not any(
            getattr(base, "__pydantic_generic_metadata__", {}).get("origin") is EventBase
            for base in cls.__mro__[1:]
        ):
            msg = (
                "Child classes of EventBase must subclass from a specialized EventBase. "
                f"'{cls.__name__}' must use EventBase[Literal[...]]."
            )
            raise TypeError(msg)

    def __new__(cls, *args: Any, **kwargs: Any) -> EventBase[Any]:  # noqa: ANN401, ARG004
        """Prevent instantiation of EventBase and its generic specializations."""
        metadata = cls.__pydantic_generic_metadata__
        if cls is EventBase or metadata.get("origin") is EventBase:
            msg = f"Can't instantiate abstract event model {cls.__name__} directly."
            raise TypeError(msg)
        return super().__new__(cls)

    def __str__(self) -> str:
        """Return a readable representation of the event model and its fields."""
        field_key_value_strs = [
            f"{field_name}={getattr(self, field_name)}" for field_name in type(self).model_fields
        ]
        return f"{self.__class__.__name__}({', '.join(field_key_value_strs)})"

    @classmethod
    def __event_type__(cls) -> Any:  # noqa: ANN401
        """Return the Pydantic field annotation for this event model."""
        return cls.model_fields["event"].annotation

    @classmethod
    def get_model_event_names(cls) -> tuple[str, ...]:
        """Return the event names declared by this model's EventBase specialization."""
        return cls.__event_names__
