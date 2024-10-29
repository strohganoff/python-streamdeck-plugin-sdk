from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from streamdeck.actions import Action, available_event_names


if TYPE_CHECKING:
    from io import TextIOWrapper

    from streamdeck.models.events import EventBase


def create_logging_action(action_uuid: str) -> Action:
    """Action that logs the event name of every occurring event."""
    logging_action = Action(action_uuid)

    action_component_name = action_uuid.split(".")[-1]
    logger = getLogger(action_component_name)

    def log_event(event_data: EventBase) -> None:
        logger.info("Action %s — event %s", logging_action.__class__, event_data.event)

    # Register the above function for every event
    for event_name in available_event_names:
        logging_action.on(event_name)(log_event)

    return logging_action


def create_file_writing_action(action_uuid: str, file: TextIOWrapper) -> Action:
    """Action that saves the full json of every occurring event."""
    file_writing_action = Action(action_uuid)

    action_component_name = action_uuid.split(".")[-1]
    logger = getLogger(action_component_name)

    def write_event(event_data: EventBase) -> None:
        logger.info("Action %s — event %s", file_writing_action.__class__, event_data.event)

        file.write(event_data.model_dump_json())
        file.write("\n")
        file.flush()

    # Register the above function for every event
    for event_name in available_event_names:
        file_writing_action.on(event_name)(write_event)

    return file_writing_action
