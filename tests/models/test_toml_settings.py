from pathlib import Path

import pytest
from pydantic import ValidationError
from pydantic_settings import PyprojectTomlConfigSettingsSource

from streamdeck.models.configs import StreamDeckToolConfig


def write_config(tmp_path, text):
    path = tmp_path / "pyproject.toml"
    path.write_text(text)
    return path


def test_discovery_and_load_isolation(tmp_path):
    from tests.data.dummy_event_listener import DummyEvent, DummyEventListener
    from tests.data.test_action1 import test_action1

    config = StreamDeckToolConfig(
        toml_file=Path(__file__).parents[1] / "data" / "pyproject.toml",
    )
    assert test_action1 in config.actions
    assert config.event_listeners == [DummyEventListener]
    assert config.event_models == [DummyEvent]
    empty = StreamDeckToolConfig(
        toml_file=write_config(tmp_path, "[tool.streamdeck]\naction_scripts = []\n"),
    )
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
        None,
        None,
        None,
        None,
    )
    assert len(sources) == 1
    assert type(sources[0]) is PyprojectTomlConfigSettingsSource


def test_explicit_path_and_override_before_import(tmp_path, monkeypatch):
    from tests.data.test_action1 import test_action1

    path = write_config(tmp_path, '[tool.streamdeck]\naction_scripts=["does.not.exist"]\n')
    monkeypatch.chdir(tmp_path.parent)
    config = StreamDeckToolConfig(
        toml_file=path, action_scripts_override=["tests.data.test_action1"]
    )
    assert config.actions == [test_action1]
    with pytest.raises(ValidationError):
        StreamDeckToolConfig(toml_file=path, action_scripts_override=[])


def test_missing_section_with_explicit_override(tmp_path):
    path = write_config(tmp_path, '[project]\nname="example"\n')
    with pytest.raises(ValidationError):
        StreamDeckToolConfig(toml_file=path)
    config = StreamDeckToolConfig(
        toml_file=path, action_scripts_override=["tests.data.test_action1"]
    )
    assert len(config.actions) == 1


def test_missing_file_is_not_silently_ignored(tmp_path):
    with pytest.raises(FileNotFoundError):
        StreamDeckToolConfig(
            toml_file=tmp_path / "missing.toml", action_scripts_override=["tests.data.test_action1"]
        )


def test_failed_load_resets_override_context(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write_config(tmp_path, "[tool.streamdeck]\naction_scripts=[]\n")
    other = tmp_path / "other.toml"
    other.write_text("[tool.streamdeck]\naction_scripts=[]\n")
    with pytest.raises(ValidationError):
        StreamDeckToolConfig(toml_file=other, action_scripts_override=["does.not.exist"])
    assert StreamDeckToolConfig().actions == []


@pytest.mark.parametrize("value", ["42", '"module"', '["does.not.exist"]'])
def test_invalid_module_values(tmp_path, value):
    path = write_config(tmp_path, "[tool.streamdeck]\naction_scripts=" + value)
    with pytest.raises(ValidationError):
        StreamDeckToolConfig(toml_file=path)
