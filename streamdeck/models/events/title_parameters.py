from __future__ import annotations

from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field

from streamdeck.models.events.base import EventBase
from streamdeck.models.events.common import DeviceSpecificEventMixin


FontStyle = Literal["", "Bold Italic", "Bold", "Italic", "Regular"]
TitleAlignment = Literal["top", "middle", "bottom"]


class TitleParameters(BaseModel):
    """Defines aesthetic properties that determine how the title should be rendered."""
    font_family: Annotated[str, Field(alias="fontFamily")]
    """Font-family the title will be rendered with."""
    font_size: Annotated[int, Field(alias="fontSize")]
    """Font-size the title will be rendered in."""
    font_style: Annotated[FontStyle, Field(alias="fontStyle")]
    """Typography of the title."""
    font_underline: Annotated[bool, Field(alias="fontUnderline")]
    """Whether the font should be underlined."""
    show_title: Annotated[bool, Field(alias="showTitle")]
    """Whether the user has opted to show, or hide the title for this action instance."""
    title_alignment: Annotated[str, Field(alias="titleAlignment")]
    """Alignment of the title."""
    title_color: Annotated[str, Field(alias="titleColor")]
    """Color of the title, represented as a hexadecimal value."""


class TitleParametersDidChangePayload(BaseModel):
    """Contextualized information for this event."""
    controller: Literal["Keypad", "Encoder"]
    """Defines the controller type the action is applicable to."""
    coordinates: dict[Literal["column", "row"], int]
    """Coordinates that identify the location of an action."""
    title: str
    """Title of the action, as specified by the user or dynamically by the plugin."""
    title_parameters: Annotated[TitleParameters, Field(alias="titleParameters")]
    """Defines aesthetic properties that determine how the title should be rendered."""
    state: Optional[int]  # noqa: UP007
    """Current state of the action; only applicable to actions that have multiple states defined within the manifest.json file."""
    settings: dict[str, Any]
    """Settings associated with the action instance."""


class TitleParametersDidChange(EventBase, DeviceSpecificEventMixin):
    """Occurs when the user updates an action's title settings in the Stream Deck application."""
    event: Literal["titleParametersDidChange"]  # type: ignore[override]
    context: str
    """Identifies the instance of an action that caused the event, i.e. the specific key or dial."""
    payload: TitleParametersDidChangePayload
