import json
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError
from pydantic_settings import CliSettingsSource, PyprojectTomlConfigSettingsSource

from streamdeck.models.configs import StreamDeckToolConfig


@pytest.fixture(autouse=True)
def plugin_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["streamdeck"])


def with_cli_actions(actions):
    return StreamDeckToolConfig(_cli_parse_args=["--action-scripts", json.dumps(actions)])


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


def test_cli_and_toml_sources_and_no_implicit_inputs(tmp_path, monkeypatch):
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
    assert [type(source) for source in sources] == [
        CliSettingsSource,
        PyprojectTomlConfigSettingsSource,
    ]


def test_cli_override_before_import(tmp_path):
    from tests.data.test_action1 import test_action1

    write_config(tmp_path, '[tool.streamdeck]\naction_scripts=["does.not.exist"]\n')
    assert with_cli_actions(["tests.data.test_action1"]).actions == [test_action1]
    with pytest.raises(ValidationError):
        StreamDeckToolConfig()


@pytest.mark.parametrize("flag", ["--event-listener", "--event-listener-modules"])
def test_cli_listener_modules_replace_toml_before_import(tmp_path, flag):
    from tests.data.dummy_event_listener import DummyEvent, DummyEventListener

    write_config(
        tmp_path,
        '[tool.streamdeck]\naction_scripts=[]\nevent_listener_modules=["does.not.exist"]\n',
    )
    config = StreamDeckToolConfig(_cli_parse_args=[flag, "tests.data.dummy_event_listener"])
    assert config.actions == []
    assert config.event_listeners == [DummyEventListener]
    assert config.event_models == [DummyEvent]
    with pytest.raises(ValidationError):
        StreamDeckToolConfig()


def test_repeated_listener_aliases_combine_in_one_override(tmp_path):
    from tests.data.dummy_event_listener import DummyEventListener
    from streamdeck.websocket import WebSocketClient

    write_config(
        tmp_path,
        '[tool.streamdeck]\naction_scripts=[]\nevent_listener_modules=["does.not.exist"]\n',
    )
    config = StreamDeckToolConfig(
        _cli_parse_args=[
            "--event-listener",
            "tests.data.dummy_event_listener",
            "--event-listener-modules",
            "streamdeck.websocket",
        ]
    )
    assert [module.__name__ for module in config.event_listener_modules] == [
        "tests.data.dummy_event_listener",
        "streamdeck.websocket",
    ]
    assert config.event_listeners == [DummyEventListener, WebSocketClient]


def test_cli_listener_override_retains_toml_actions(tmp_path):
    from tests.data.test_action1 import test_action1

    write_config(tmp_path, '[tool.streamdeck]\naction_scripts=["tests.data.test_action1"]\n')
    config = StreamDeckToolConfig(
        _cli_parse_args=[
            "--event-listener",
            "tests.data.dummy_event_listener",
        ]
    )
    assert config.actions == [test_action1]


def test_filtered_cli_accepts_repeated_actions_and_ignores_host_args(tmp_path):
    from tests.data.test_action1 import test_action1
    from tests.data.test_action2 import test_action2, test_global_action1

    write_config(tmp_path, '[tool.streamdeck]\naction_scripts=["does.not.exist"]\n')
    config = StreamDeckToolConfig(
        _cli_parse_args=[
            "-port",
            "12345",
            "-info",
            '{"plugin":{"uuid":"example"}}',
            "--action-scripts",
            "tests.data.test_action1",
            "--action-scripts",
            "tests.data.test_action2",
            "--debug",
            "5678",
        ]
    )
    assert config.actions == [test_action1, test_action2, test_global_action1]


@pytest.mark.parametrize("flag", ["--help", "-h"])
def test_filtered_cli_help_exposes_only_module_options(tmp_path, capsys, flag):
    write_config(tmp_path, "[tool.streamdeck]\naction_scripts=[]\n")
    with pytest.raises(SystemExit) as exc:
        StreamDeckToolConfig(_cli_parse_args=[flag])
    assert exc.value.code == 0
    help_text = capsys.readouterr().out
    assert "--action-scripts" in help_text
    assert "--event-listener" in help_text
    assert "--event-listener-modules" in help_text
    assert "--debug" not in help_text


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
