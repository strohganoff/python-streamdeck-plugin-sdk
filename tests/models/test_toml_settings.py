import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from pydantic_settings import CliSettingsSource, PyprojectTomlConfigSettingsSource

from streamdeck.models.configs import StreamDeckToolConfig


@pytest.fixture(autouse=True)
def plugin_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def with_cli_actions(actions):
    source = CliSettingsSource(
        StreamDeckToolConfig,
        cli_kebab_case=True,
        cli_parse_args=["--action-scripts", json.dumps(actions)],
    )
    return StreamDeckToolConfig(_cli_settings_source=source)


def write_config(tmp_path, text):
    path = tmp_path / "pyproject.toml"
    path.write_text(text)
    return path


def test_discovery_and_load_isolation(tmp_path):
    from tests.data.dummy_event_listener import DummyEvent, DummyEventListener
    from tests.data.test_action1 import test_action1

    fixture = Path(__file__).resolve().parents[1] / "data" / "pyproject.toml"
    (tmp_path / "pyproject.toml").write_text(fixture.read_text())
    config = StreamDeckToolConfig()
    assert test_action1 in config.actions
    assert config.event_listeners == [DummyEventListener]
    assert config.event_models == [DummyEvent]
    write_config(tmp_path, "[tool.streamdeck]\naction_scripts = []\n")
    empty = StreamDeckToolConfig()
    assert empty.actions == empty.event_listeners == empty.event_models == []
    assert test_action1 in config.actions


def test_only_toml_source_and_no_implicit_inputs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write_config(tmp_path, "[tool.streamdeck]\naction_scripts = []\n")
    monkeypatch.setenv("ACTION_SCRIPTS", '["does.not.exist"]')
    (tmp_path / ".env").write_text('ACTION_SCRIPTS=["does.not.exist"]\n')
    secrets = tmp_path / "secrets"
    secrets.mkdir()
    (secrets / "action_scripts").write_text('["does.not.exist"]')
    config = StreamDeckToolConfig(
        action_scripts=["does.not.exist"],
        _env_file=tmp_path / ".env",
        _secrets_dir=secrets,
    )
    assert config.actions == []
    sources = StreamDeckToolConfig.settings_customise_sources(
        StreamDeckToolConfig,
    )
    assert len(sources) == 1
    assert type(sources[0]) is PyprojectTomlConfigSettingsSource


def test_cli_override_before_import(tmp_path):
    from tests.data.test_action1 import test_action1

    write_config(tmp_path, '[tool.streamdeck]\naction_scripts=["does.not.exist"]\n')
    assert with_cli_actions(["tests.data.test_action1"]).actions == [test_action1]
    with pytest.raises(ValidationError):
        StreamDeckToolConfig()


def test_missing_section_with_cli_values(tmp_path):
    write_config(tmp_path, '[project]\nname="example"\n')
    with pytest.raises(ValidationError):
        StreamDeckToolConfig()
    assert len(with_cli_actions(["tests.data.test_action1"]).actions) == 1


def test_missing_file_uses_cli_or_reports_missing_fields():
    with pytest.raises(ValidationError):
        StreamDeckToolConfig()
    assert len(with_cli_actions(["tests.data.test_action1"]).actions) == 1


def test_failed_cli_load_does_not_affect_next_load(tmp_path):
    write_config(tmp_path, "[tool.streamdeck]\naction_scripts=[]\n")
    with pytest.raises(ValidationError):
        with_cli_actions(["does.not.exist"])
    assert StreamDeckToolConfig().actions == []


def test_only_working_directory_toml_is_used(tmp_path, monkeypatch):
    write_config(tmp_path, "[tool.streamdeck]\naction_scripts=[]\n")
    child = tmp_path / "child"
    child.mkdir()
    monkeypatch.chdir(child)
    with pytest.raises(ValidationError):
        StreamDeckToolConfig(toml_file=tmp_path / "pyproject.toml")


@pytest.mark.parametrize("value", ["42", '"module"', '["does.not.exist"]'])
def test_invalid_module_values(tmp_path, value):
    write_config(tmp_path, "[tool.streamdeck]\naction_scripts=" + value)
    with pytest.raises(ValidationError):
        StreamDeckToolConfig()
