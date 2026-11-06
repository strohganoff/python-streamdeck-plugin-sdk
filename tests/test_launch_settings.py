import json
import subprocess
import sys
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from streamdeck.models.configs import StreamDeckToolConfig
from streamdeck.models.launch import parse_launch_arguments


def host_args(port_flag="-port"):
    return [
        port_flag,
        "12345",
        "-pluginUUID",
        "registration-id",
        "-registerEvent",
        "registerPlugin",
        "-info",
        json.dumps({"plugin": {"uuid": "com.example.plugin"}}),
    ]


@pytest.mark.parametrize("port_flag", ["-port", "-p"])
@pytest.mark.parametrize("debug_flag", ["--debug", "-d"])
def test_host_flags_and_development_options(tmp_path, port_flag, debug_flag):
    launch = parse_launch_arguments(
        host_args(port_flag)
        + [
            "--plugin-dir",
            str(tmp_path),
            debug_flag,
            "5678",
            "--action-scripts",
            "example.actions",
            "--action-scripts",
            "example.other",
        ]
    )
    assert launch.port == 12345
    assert launch.plugin_registration_uuid == "registration-id"
    assert launch.register_event == "registerPlugin"
    assert launch.info == {"plugin": {"uuid": "com.example.plugin"}}
    assert launch.plugin_dir == tmp_path
    assert launch.debug_port == 5678
    assert launch.action_scripts == ["example.actions", "example.other"]


def test_defaults_are_resolved_at_parse_time(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PORT", "9999")
    monkeypatch.setenv("ACTION_SCRIPTS", '["does.not.exist"]')
    monkeypatch.setenv("action_scripts", '["does.not.exist"]')
    monkeypatch.setenv("debug", "5678")
    launch = parse_launch_arguments(host_args())
    assert launch.plugin_dir == tmp_path
    assert launch.port == 12345
    assert launch.action_scripts is None
    assert launch.debug_port is None


@pytest.mark.parametrize("module", ["streamdeck", "streamdeck.utils.helper_actions"])
def test_cli_help_and_helper_import_in_fresh_process(module):
    args = ["-m", module, "--help"] if module == "streamdeck" else ["-c", f"import {module}"]
    result = subprocess.run([sys.executable, *args], capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
    if module == "streamdeck":
        assert "usage:" in result.stdout.lower()
        assert "--help" in result.stdout


def test_plugin_directory_rejects_a_file(tmp_path, capsys):
    path = tmp_path / "file.txt"
    path.write_text("not a directory")
    with pytest.raises(SystemExit) as exc:
        parse_launch_arguments(host_args() + ["--plugin-dir", str(path)])
    assert exc.value.code == 2
    assert "Path does not point to a directory" in capsys.readouterr().err


@pytest.mark.parametrize("change", ["missing", "port", "json", "identity", "unknown", "directory"])
def test_invalid_launch_exits_before_startup(tmp_path, capsys, change):
    args = host_args()
    if change == "missing":
        args = args[2:]
    elif change == "port":
        args[1] = "invalid"
    elif change == "json":
        args[-1] = "{invalid"
    elif change == "identity":
        args[-1] = "{}"
    elif change == "unknown":
        args += ["--unknown"]
    else:
        args += ["--plugin-dir", str(tmp_path / "missing")]
    with pytest.raises(SystemExit) as exc:
        parse_launch_arguments(args)
    assert exc.value.code == 2
    assert "error:" in capsys.readouterr().err


def test_help_does_not_require_host_arguments(capsys):
    with pytest.raises(SystemExit) as exc:
        parse_launch_arguments(["--help"])
    assert exc.value.code == 0
    help_text = capsys.readouterr().out
    for name in ("-port", "-pluginUUID", "-registerEvent", "-info", "--action-scripts", "--debug"):
        assert name in help_text


def test_cli_precedence_does_not_import_invalid_toml_action(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        '[tool.streamdeck]\naction_scripts=["does.not.exist"]\n'
    )
    launch = parse_launch_arguments(host_args() + ["--action-scripts", "tests.data.test_action1"])
    assert len(StreamDeckToolConfig(_cli_settings_source=launch.cli_settings_source).actions) == 1
    with pytest.raises(ValidationError):
        StreamDeckToolConfig()


def test_omitted_cli_actions_preserve_toml(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        '[tool.streamdeck]\naction_scripts=["tests.data.test_action1"]\n'
    )
    launch = parse_launch_arguments(host_args())
    assert len(StreamDeckToolConfig(_cli_settings_source=launch.cli_settings_source).actions) == 1


def test_launcher_imports_from_plugin_directory_and_registers_listeners_first(
    tmp_path, monkeypatch
):
    import streamdeck.__main__ as entry

    import_dir = tmp_path / "imports"
    import_dir.mkdir()
    monkeypatch.chdir(tmp_path)
    (import_dir / "pyproject.toml").write_text(
        '[tool.streamdeck]\naction_scripts=["does.not.exist"]\n'
    )
    (import_dir / "local_plugin_actions.py").write_text(
        'from streamdeck.event_handlers.actions import Action\naction = Action("example.action")\n'
    )
    (tmp_path / "pyproject.toml").write_text(
        '[tool.streamdeck]\naction_scripts=["does.not.exist"]\n'
        'event_listener_modules=["tests.data.dummy_event_listener"]\n'
    )
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "streamdeck",
            *host_args(),
            "--plugin-dir",
            str(import_dir),
            "--action-scripts",
            "local_plugin_actions",
            "-d",
            "5678",
        ],
    )
    manager = Mock()
    factory = Mock(return_value=manager)
    monkeypatch.setattr(entry, "PluginManager", factory)
    monkeypatch.setattr(entry, "configure_streamdeck_logger", Mock())
    debug = Mock()
    monkeypatch.setattr(entry, "setup_debug_mode", debug)
    try:
        entry.plugin()
        assert [call[0] for call in manager.mock_calls] == [
            "register_event_listener",
            "register_action",
            "run",
        ]
        assert factory.call_args.kwargs["port"] == 12345
        assert factory.call_args.kwargs["plugin_uuid"] == "com.example.plugin"
        assert factory.call_args.kwargs["plugin_registration_uuid"] == "registration-id"
        debug.assert_called_once_with(5678)
    finally:
        sys.modules.pop("local_plugin_actions", None)
