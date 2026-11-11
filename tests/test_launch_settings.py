import json
import subprocess
import sys
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from streamdeck.models.configs import StreamDeckToolConfig
from streamdeck.models.launch import LaunchArguments


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
@pytest.mark.parametrize("listener_flag", ["--event-listener", "--event-listener-modules"])
def test_host_flags_and_development_options(tmp_path, port_flag, debug_flag, listener_flag):
    launch = LaunchArguments(
        _cli_parse_args=host_args(port_flag)
        + [
            "--plugin-dir",
            str(tmp_path),
            debug_flag,
            "5678",
            "--action-scripts",
            "example.actions",
            "--action-scripts",
            "example.other",
            listener_flag,
            "example.listener_a",
            listener_flag,
            "example.listener_b",
        ]
    )
    assert launch.port == 12345
    assert launch.plugin_registration_uuid == "registration-id"
    assert launch.register_event == "registerPlugin"
    assert launch.info.plugin_uuid == "com.example.plugin"
    assert launch.plugin_dir == tmp_path
    assert launch.debug_port == 5678
    assert launch.action_scripts == ["example.actions", "example.other"]
    assert launch.event_listener_modules == ["example.listener_a", "example.listener_b"]


def test_defaults_are_resolved_at_parse_time(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PORT", "9999")
    monkeypatch.setenv("ACTION_SCRIPTS", '["does.not.exist"]')
    monkeypatch.setenv("action_scripts", '["does.not.exist"]')
    monkeypatch.setenv("debug", "5678")
    launch = LaunchArguments(_cli_parse_args=host_args())
    assert launch.plugin_dir == tmp_path
    assert launch.port == 12345
    assert launch.action_scripts is None
    assert launch.event_listener_modules is None
    assert launch.debug_port is None


def test_launch_sources_exclude_constructor_dotenv_and_secrets(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text('debug=9999\naction_scripts=["does.not.exist"]\n')
    secrets = tmp_path / "secrets"
    secrets.mkdir()
    (secrets / "debug").write_text("9999")
    launch = LaunchArguments(
        _cli_parse_args=host_args(),
        _env_file=tmp_path / ".env",
        _secrets_dir=secrets,
        port=9999,
        action_scripts=["does.not.exist"],
    )
    assert launch.port == 12345
    assert launch.action_scripts is None
    assert launch.event_listener_modules is None
    assert launch.debug_port is None


@pytest.mark.parametrize(
    "info",
    [
        {},
        {"plugin": None},
        {"plugin": []},
        {"plugin": {}},
        {"plugin": {"uuid": None}},
        {"plugin": {"uuid": 123}},
        {"plugin": {"uuid": {}}},
    ],
)
def test_registration_info_requires_nested_string_uuid(info):
    args = host_args()
    args[-1] = json.dumps(info)
    with pytest.raises(ValidationError) as exc:
        LaunchArguments(_cli_parse_args=args)
    assert "info.plugin.uuid" in str(exc.value)


def test_registration_info_extracts_only_used_fields():
    args = host_args()
    args[-1] = json.dumps(
        {
            "plugin": {"uuid": "com.example.plugin", "version": "1.2.3"},
            "application": {"platform": "mac", "version": "7.0"},
            "devices": [],
            "colors": {},
            "devicePixelRatio": 2,
        }
    )
    launch = LaunchArguments(_cli_parse_args=args)
    assert launch.info.plugin_uuid == "com.example.plugin"
    assert launch.info.model_dump() == {"plugin_uuid": "com.example.plugin"}


@pytest.mark.parametrize("module", ["streamdeck", "streamdeck.utils.helper_actions"])
def test_cli_help_and_helper_import_in_fresh_process(module):
    args = ["-m", module, "--help"] if module == "streamdeck" else ["-c", f"import {module}"]
    result = subprocess.run([sys.executable, *args], capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
    if module == "streamdeck":
        assert "usage:" in result.stdout.lower()
        assert "--help" in result.stdout


def test_plugin_directory_rejects_a_file(tmp_path):
    path = tmp_path / "file.txt"
    path.write_text("not a directory")
    with pytest.raises(ValidationError) as exc:
        LaunchArguments(_cli_parse_args=host_args() + ["--plugin-dir", str(path)])
    assert "Path does not point to a directory" in str(exc.value)


@pytest.mark.parametrize("change", ["missing", "port", "json", "identity", "unknown", "directory"])
def test_invalid_launch_exits_before_startup(tmp_path, capsys, caplog, monkeypatch, change):
    from streamdeck.__main__ import main

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
    monkeypatch.setattr(sys, "argv", ["streamdeck", *args])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2
    if change in ("missing", "unknown"):
        assert capsys.readouterr().err
    else:
        assert "Invalid launch arguments:" in caplog.text


def test_help_does_not_require_host_arguments(capsys):
    with pytest.raises(SystemExit) as exc:
        LaunchArguments(_cli_parse_args=["--help"])
    assert exc.value.code == 0
    help_text = capsys.readouterr().out
    for name in ("-port", "-pluginUUID", "-registerEvent", "-info", "--action-scripts", "--debug"):
        assert name in help_text
    assert "--event-listener" in help_text


def test_cli_precedence_does_not_import_invalid_toml_action(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        '[tool.streamdeck]\naction_scripts=["does.not.exist"]\n'
    )
    monkeypatch.setattr(
        sys, "argv", ["streamdeck", *host_args(), "--action-scripts", "tests.data.test_action1"]
    )
    assert len(StreamDeckToolConfig().actions) == 1
    with pytest.raises(ValidationError):
        StreamDeckToolConfig(_cli_parse_args=[])


def test_omitted_cli_actions_preserve_toml(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        '[tool.streamdeck]\naction_scripts=["tests.data.test_action1"]\n'
    )
    monkeypatch.setattr(sys, "argv", ["streamdeck", *host_args()])
    assert len(StreamDeckToolConfig().actions) == 1


@pytest.mark.parametrize("explicit_args", [False, True])
def test_launcher_imports_from_plugin_directory_and_registers_listeners_first(
    tmp_path, monkeypatch, explicit_args
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
        'event_listener_modules=["does.not.exist"]\n'
    )
    monkeypatch.setattr(sys, "path", list(sys.path))
    args = [
        *host_args(),
        "--plugin-dir",
        str(import_dir),
        "--action-scripts",
        "local_plugin_actions",
        "--event-listener",
        "tests.data.dummy_event_listener",
        "-d",
        "5678",
    ]
    process_args = ["--unrelated-process-argument"] if explicit_args else args
    monkeypatch.setattr(sys, "argv", ["streamdeck", *process_args])
    manager = Mock()
    factory = Mock(return_value=manager)
    monkeypatch.setattr(entry, "PluginManager", factory)
    monkeypatch.setattr(entry, "configure_streamdeck_logger", Mock())
    debug = Mock()
    monkeypatch.setattr(entry, "setup_debug_mode", debug)
    try:
        entry.main(args) if explicit_args else entry.main()
        assert [call[0] for call in manager.mock_calls] == [
            "register_event_listener",
            "register_action",
            "run",
        ]
        assert factory.call_args.kwargs["port"] == 12345
        assert factory.call_args.kwargs["plugin_uuid"] == "com.example.plugin"
        assert factory.call_args.kwargs["plugin_registration_uuid"] == "registration-id"
        assert factory.call_args.kwargs["info"] == {"plugin_uuid": "com.example.plugin"}
        debug.assert_called_once_with(5678)
    finally:
        sys.modules.pop("local_plugin_actions", None)


@pytest.mark.parametrize("phase", ["settings", "listener", "action", "run"])
def test_main_logs_startup_and_runtime_failures(monkeypatch, caplog, phase):
    import streamdeck.__main__ as entry

    error = RuntimeError(f"{phase} failed")
    listener_type = Mock()
    config = Mock(event_listeners=[listener_type], actions=[object()], injectable_handler_params={})
    settings_factory = Mock(return_value=config)
    manager = Mock()
    if phase == "settings":
        settings_factory.side_effect = error
    elif phase == "listener":
        listener_type.side_effect = error
    elif phase == "action":
        manager.register_action.side_effect = error
    else:
        manager.run.side_effect = error

    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.setattr(entry, "configure_streamdeck_logger", Mock())
    monkeypatch.setattr(entry, "StreamDeckToolConfig", settings_factory)
    monkeypatch.setattr(entry, "PluginManager", Mock(return_value=manager))
    with pytest.raises(RuntimeError) as exc:
        entry.main(host_args())
    assert exc.value is error
    assert "Plugin startup or execution failed" in caplog.text


def test_run_plugin_uses_supplied_settings_without_reading_process_args(tmp_path, monkeypatch):
    import streamdeck.__main__ as entry

    monkeypatch.chdir(tmp_path)
    launch = LaunchArguments(_cli_parse_args=host_args())
    config = StreamDeckToolConfig(
        _cli_parse_args=[
            "--action-scripts",
            "tests.data.test_action1",
            "--event-listener",
            "tests.data.dummy_event_listener",
        ]
    )
    monkeypatch.setattr(sys, "argv", ["unrelated-program", "--invalid"])
    manager = Mock()
    monkeypatch.setattr(entry, "PluginManager", Mock(return_value=manager))
    entry.run_plugin(launch, config)
    assert [call[0] for call in manager.mock_calls] == [
        "register_event_listener",
        "register_action",
        "run",
    ]
