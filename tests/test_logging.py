"""This module contains tests for configuring loggers for the Elgato Stream Deck plugins.

The tests validate that the logger configurations correctly create log files for both local plugin-specific logging and
centralized Stream Deck logging.
"""
import logging
from pathlib import Path

import platformdirs
import pytest
from streamdeck.utils.logging import configure_local_logger, configure_streamdeck_logger


@pytest.fixture
def fake_plugin_local_log_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Fixture to set up a fake local log directory for plugin-specific logging.

    This fixture uses `monkeypatch` to replace the `platformdirs.user_data_path` function, redirecting it to use a
    temporary path for testing purposes.

    Args:
        monkeypatch (pytest.MonkeyPatch): The pytest monkeypatch object for modifying module attributes.
        tmp_path (Path): A temporary path provided by pytest for file operations.

    Returns:
        Path: The temporary path used for local plugin logging.
    """
    monkeypatch.setattr(
        platformdirs, "user_data_path", value=(lambda plugin_uuid: tmp_path / plugin_uuid)
    )
    return tmp_path


@pytest.fixture
def fake_streamdeck_log_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Fixture to set up a fake Stream Deck log directory for centralized logging.

    This fixture uses `monkeypatch` to replace the `platformdirs.user_log_path` function, redirecting it to use a
    temporary path for testing purposes.

    Args:
        monkeypatch (pytest.MonkeyPatch): The pytest monkeypatch object for modifying module attributes.
        tmp_path (Path): A temporary path provided by pytest for file operations.

    Returns:
        Path: The temporary path used for Stream Deck logging.
    """
    monkeypatch.setattr(platformdirs, "user_log_path", value=(lambda appname: tmp_path / appname))
    return tmp_path


def test_local_logger(fake_plugin_local_log_dir: Path):
    """Test the configuration of a local plugin-specific logger.

    This test verifies that a logger configured for a specific plugin writes logs to the correct local directory.

    Args:
        fake_plugin_local_log_dir (Path): The fake local log directory path provided by the fixture.
    """
    FAKE_LOGGER_NAME = "TEST-PLUGIN-FILE"
    FAKE_PLUGIN_UUID = "com.test.spotifier"
    LOG_STATEMENT = "Test log."

    configure_local_logger(name=FAKE_LOGGER_NAME, plugin_uuid=FAKE_PLUGIN_UUID)
    logger = logging.getLogger(FAKE_LOGGER_NAME)

    logger.info(LOG_STATEMENT)

    plugin_component_name = FAKE_PLUGIN_UUID.split(".")[-1]

    log_file = (
        fake_plugin_local_log_dir
        / "com.elgato.StreamDeck/Plugins"
        / f"{FAKE_PLUGIN_UUID}.sdPlugin"
        / f"logs/{plugin_component_name}.log"
    )

    assert log_file.exists()

    with log_file.open("r") as f:
        actual_log_file_output = f.read()
        # We don't want to make too many assumptions here about the format of the log output.
        assert "INFO" in actual_log_file_output
        assert LOG_STATEMENT in actual_log_file_output
        # Probably don't need to assert that the logger's name is in the log.
        # assert fake_name in actual_log_file_output


def test_streamdeck_logger(fake_streamdeck_log_dir: Path):
    """Test the configuration of a centralized Stream Deck logger.

    This test verifies that a logger configured for the Stream Deck writes logs to the correct centralized directory.

    Args:
        fake_streamdeck_log_dir (Path): The fake Stream Deck log directory path provided by the fixture.
    """
    FAKE_LOGGER_NAME = "my_test_name"
    FAKE_PLUGIN_UUID = "com.test.plugin"
    LOG_STATEMENT = "Testing 123..."

    configure_streamdeck_logger(name=FAKE_LOGGER_NAME, plugin_uuid=FAKE_PLUGIN_UUID)
    logger = logging.getLogger(FAKE_LOGGER_NAME)

    logger.info(LOG_STATEMENT)

    log_file = fake_streamdeck_log_dir / "ElgatoStreamDeck" / f"{FAKE_PLUGIN_UUID}.log"

    assert log_file.exists()
    with log_file.open("r") as f:
        actual_log_file_output = f.read()
        # We don't want to make too many assumptions here about the format of the log output.
        assert "INFO" in actual_log_file_output
        assert LOG_STATEMENT in actual_log_file_output
        # Probably don't need to assert that the logger's name is in the log.
        assert FAKE_LOGGER_NAME in actual_log_file_output
