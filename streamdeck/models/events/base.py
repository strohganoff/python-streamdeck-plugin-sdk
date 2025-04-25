from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Literal
from weakref import WeakValueDictionary

from pydantic import BaseModel, ConfigDict, create_model
from typing_extensions import LiteralString, TypedDict, override  # noqa: UP035


if TYPE_CHECKING:
    from typing import Any, ClassVar



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


class EventMetadataDict(TypedDict):
    """Metadata for specialized EventBase submodels.

    Similar to the __pydantic_generic_metadata__ attribute, but for use in the EventBase class——which isn't actually generic.
    """
    origin: type[EventBase]
    """Origin class of the specialized EventBase submodel."""
    args: tuple[str, ...]
    """Event names for the specialized EventBase submodel."""


if TYPE_CHECKING:
    # Because we can't override a BaseModel's metaclass __getitem__ method without angering Pydantic during runtime,
    # we define this stub here to satisfy static type checkers that introspect the metaclass method annotations
    # to determine expected types in the class subscriptions.

    from collections.abc import Callable

    from pydantic._internal._model_construction import ModelMetaclass  # type: ignore[import]

    from streamdeck.types import EventNameStr

    class EventMeta(ModelMetaclass):
        """Metaclass for EventBase stub to satisfy static type checkers."""
        @classmethod
        def __getitem__(cls, event_names: LiteralString | tuple[LiteralString, ...]) -> type[EventBase]: ...

    class EventBase(BaseModel, metaclass=EventMeta):
        """Base class for all event models.

        EventBase itself should not be instantiated, nor should it be subclassed directly.
        Instead, use a subscripted subclass of EventBase, e.g. `EventBase["eventName"]`, to subclass from.

        Examples:
        ```
        class KeyDown(EventBase["keyDown"]):
            # 'event' field's type annotation is internally set here as `Literal["keyDown"]`
            ...

        class TestEvent(EventBase["test", "testing"]):
            # 'event' field's type annotation is internally set here as `Literal["test", "testing"]`
            ...

        ```
        """
        event: EventNameStr
        """Name of the event used to identify what occurred.

        Subclass models must define this field as a Literal type with the event name string that the model represents.
        """
        __event_metadata__: ClassVar[EventMetadataDict]
        """Metadata for specialized EventBase submodels."""
        __event_type__: ClassVar[Callable[[], type[object] | None]]
        """Return the event type for the event model."""

        @classmethod
        def get_model_event_names(cls) -> tuple[EventNameStr, ...]:
            """Return the event names for the event model."""
            ...

else:
    class EventBase(ConfiguredBaseModel, ABC):
        """Base class for all event models.

        EventBase itself should not be instantiated, nor should it be subclassed directly.
        Instead, use a subscripted subclass of EventBase, e.g. `EventBase["eventName"]`, to subclass from.

        Examples:
        ```
        class KeyDown(EventBase["keyDown"]):
            # 'event' field's type annotation is internally set here as `Literal["keyDown"]`
            ...

        class TestEvent(EventBase["test", "testing"]):
            # 'event' field's type annotation is internally set here as `Literal["test", "testing"]`
            ...

        ```
        """
        # A weak reference dictionary to store subscripted subclasses of EventBase. Weak references are used to minimize memory usage.
        _cached_specialized_submodels: ClassVar[WeakValueDictionary[str, type[EventBase]]] = WeakValueDictionary()
        __event_metadata__: ClassVar[EventMetadataDict]
        """Metadata for specialized EventBase submodels."""

        event: str
        """Name of the event used to identify what occurred.

        Subclass models must define this field as a Literal type with the event name string that the model represents.
        """

        def __new__(cls, *args: Any, **kwargs: Any) -> EventBase:
            """Create a new instance of the event model.

            This method is called when the model is instantiated.
            It validates that the event name is a string and not empty.
            """
            if cls is EventBase:
                raise TypeError("Can't instantiate abstract class EventBase directly.")
            if EventBase in cls.__bases__:
                raise TypeError(f"Can't instantiate abstract subscripted EventBase class {cls.__name__} directly.")
            return super().__new__(cls)

        @override
        @classmethod
        def __class_getitem__(cls: type[EventBase], event_names: LiteralString | tuple[LiteralString, ...]) -> type[EventBase]: # type: ignore[override]
            """Create a subclass alias of EventBase with the given event names.

            This method is called when the class is subscripted.
            If the event names are not already registered, a new subclass is created.
            Validations are performed to ensure that the event names are strings and not empty, and that the subscripted class is not a subclass of EventBase.
            """
            if cls is not EventBase: # type: ignore[misc]
                raise TypeError(f"Subclasses of EventBase are not subscriptable — '{cls.__name__}'")  # noqa: TRY003, EM102

            # Whether event_names is a string or tuple of strings, validate that it/they is/are a string
            if not isinstance(event_names, tuple):
                event_names = (event_names,)

            # Validate that all event names are strings
            if any(not isinstance(name, str) for name in event_names): # type: ignore[misc]
                raise TypeError(f"Event names must be strings, not {type(event_names).__name__}; args: {event_names}")  # noqa: TRY003, EM102

            subtype_name = f"{cls.__name__}[{event_names}]"

            return cls.__new_subscripted_base__(subtype_name, event_names)

        @classmethod
        def __new_subscripted_base__(cls: type[EventBase], new_name: str, event_name_args: tuple[str, ...]) -> type[EventBase]:
            """Dynamically create a new Singleton subclass of EventBase with the given event names for the event field.

            Only create a new subscripted subclass if it doesn't already exist in the _cached_specialized_submodels dictionary, otherwise return the existing subclass.
            The new subclasses created here will be ignored in the __init_subclass__ method.
            """
            if new_name not in cls._cached_specialized_submodels:
                # Make sure not to pass in a value `_cached_specialized_submodels` in the create_model() call, in order to avoid shadowing the class variable.
                cls._cached_specialized_submodels[new_name] = create_model(
                    new_name,
                    __base__=cls,
                    __event_metadata__=(EventMetadataDict, {"origin": cls, "args": event_name_args}),
                    event=(Literal[event_name_args], ...),
                    __cls_kwargs__={"_is_specialized_base": True},  # This gets passed to __init_subclass__ as a kwarg to indicate that this is a specialized (subscripted) subclass of EventBase.
                )

            return cls._cached_specialized_submodels[new_name]

        @classmethod
        def __init_subclass__(cls, _is_specialized_base: bool = False) -> None:
            """Validate a child class of EventBase (not a subscripted base subclass) is subclassing from a subscripted EventBase.

            Args:
                _is_specialized_base: Whether this is a specialized submodel of EventBase (i.e., a subscripted subclass).
                    This should only be True for the subscripted subclasses created in __class_getitem__.
            """
            if _is_specialized_base:
                # This is a subscripted subclass of EventBase, so we don't need to do anything.
                return

            if EventBase in cls.__bases__:
                # Normally, only subscripted subclasses of EventBase (filtered out above) will have (un-subscripted) EventBase in their __bases__.
                # If we get here, it means that this is a subclass of EventBase that is not subscripted, which is not allowed.
                msg = f"Child classes of EventBase cannot subclass from non-subscripted EventBase. '{cls.__name__}' must subclass from a subscripted EventBase."
                raise TypeError(msg)

        def __str__(self) -> str:
            """Return a string representation of the event model in the format 'EventName(event=event_name, field_name=field_value, etc.)'."""
            field_key_value_strs: list[str] = [f"{field_name}={getattr(self, field_name)}" for field_name in type(self).model_fields]
            return f"{self.__class__.__name__}({', '.join(field_key_value_strs)})"

        @classmethod
        def __event_type__(cls) -> type[object] | None:
            """Return the event type for the event model."""
            return cls.model_fields["event"].annotation

        @classmethod
        def get_model_event_names(cls) -> tuple[str, ...]:
            """Return the event names for the event model."""
            return cls.__event_metadata__["args"]
