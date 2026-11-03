# Plugin configuration

The Typer launcher loads the plugin directory's `pyproject.toml` through
[`StreamDeckToolConfig`](streamdeck/models/configs.py). Its only configured
settings source is `PyprojectTomlConfigSettingsSource`, selecting
`[tool.streamdeck]`. Constructor field values, environment variables, dotenv
files, secrets, and Pydantic Settings CLI parsing are not sources in this phase.
Typer continues to parse the existing launch flags.

```toml
[tool.streamdeck]
action_scripts = ["myplugin.actions"]
event_listener_modules = ["myplugin.listeners"]
```

```python
from pathlib import Path
from streamdeck.models.configs import StreamDeckToolConfig

config = StreamDeckToolConfig(
    toml_file=Path("/path/to/plugin/pyproject.toml"),
)
actions = config.actions
listeners = config.event_listeners
event_models = config.event_models
```

The plugin directory must be importable before loading these settings; the CLI
adds it to `sys.path` first. Nonempty Typer `action_scripts` overrides explicitly
replace the TOML source's action list before module imports and validation.
Omitted or empty overrides retain the TOML value. An explicit file must exist,
including when overriding actions. The override can supply actions when the
TOML section is absent. Unknown TOML settings remain ignored.

`PyProjectConfigs`, `ToolSection`, and their forwarding properties have been
removed. Use `StreamDeckToolConfig` directly. Discovery lists are now derived
from each settings instance, fixing accumulation across repeated loads. Discovery
still includes imported objects and does not deduplicate them. Event models
still reach the manager through registered listeners' `event_models`.

Regression coverage is in
[`test_toml_settings.py`](tests/models/test_toml_settings.py). These tests use
local modules and do not establish live Stream Deck integration.

Validation on 2026-11-02 used Python 3.9.6. A clean export of the staged files
passed all 141 tests; the nine configuration regression cases also passed with
Pydantic 2.11.0 and Pydantic Settings 2.11.0. Source and wheel builds succeeded,
and both installed CLI help entry points worked outside the checkout. Ruff
passed for `streamdeck/models/configs.py`. Other Python versions and live
Stream Deck startup were not exercised.
