"""This module provides dynamic versioning for the package, intended for use in GitHub Actions during a release event.

The version is extracted from the release tag in the GitHub event data.
If this ins't a release, or isn't running in a GitHub runner, or something is missing,
the script will fall back to version "0.0.1", to allow for testing.

Future Improvements:
- I may either improve this to handle local building as well as merging into 'main' branch,
    or just go with setuptools_scm to replace all of this.
"""
from __future__ import annotations

import json
import logging
import os


# NOTE: A single variable is set using this function below.
def get_version():
    """Retrieve the version from GitHub Actions environment variables.

    Raises:
        RuntimeError: If not running in GitHub Actions or the event is not a release.
        FileNotFoundError: If the GitHub event path file is not found.
        json.JSONDecodeError: If the event data cannot be parsed as JSON.
        ValueError: If the release tag is not found in the event data.

    Returns:
        str: The version extracted from the release tag.
    """
    if os.getenv("GITHUB_ACTIONS") != "true":
        logging.error("Missing $GITHUB_ACTIONS environment variable. This script must (currently) be run in a GitHub Actions environment.")
        return "0.0.1"
    # May restrict the event type in the future.
    # if os.getenv("GITHUB_EVENT_NAME") != "release":
    #     logging.error("Missing $GITHUB_EVENT_NAME environment variable or not a release event. This script must (currently) be triggered by a release event.")
    #     return "0.0.1"

    event_path = os.getenv("GITHUB_EVENT_PATH")

    if not event_path:
        logging.error("Missing $GITHUB_EVENT_PATH environment variable. Unable to locate the GitHub event data file.")
        return "0.0.1"

    try:
        with open(event_path) as f:
            event_data = json.load(f)
    except FileNotFoundError as e:
        logging.exception("Error reading event data from file.")
        return "0.0.1"
    except json.JSONDecodeError as e:
        logging.exception("Error parsing event data as JSON.")
        return "0.0.1"

    # May restrict the action type in the future.
    # if event_data.get("action") != "published":
    #     return "0.0.1"

    tag_name = event_data.get("release", {}).get("tag_name")

    if not tag_name:
        logging.error("No tag version found in event_data file.")
        return "0.0.1"

    return tag_name.lstrip("v")


MODULE_VERSION = get_version()
