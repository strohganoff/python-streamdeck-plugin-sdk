# Plugin configuration

The launcher parses arguments with Pydantic Settings through
[`LaunchArguments`](streamdeck/models/launch.py), then loads the working
directory's `pyproject.toml` through
[`StreamDeckToolConfig`](streamdeck/models/configs.py). Plugin settings sources
are a filtered `CliSettingsSource`, followed by
`PyprojectTomlConfigSettingsSource`, selecting `[tool.streamdeck]`. Constructor
field values, environment variables, dotenv files, and secrets are not sources.

Model fields use pipe-syntax unions. The package requires Python 3.10 or later.

`LaunchArguments` inherits from `BaseSettings`: `LaunchArguments()` parses and
validates the process arguments during construction. Tests and programmatic
launchers can supply `LaunchArguments(_cli_parse_args=[...])`. The model excludes
all non-CLI sources. `settings_customise_sources()` directly returns the
customized CLI source; the model uses the standard `BaseSettings` constructor.
The entry point reports validation failures as CLI errors. Plugin settings
independently parse the same process arguments to obtain action and listener
module overrides.

```toml
[tool.streamdeck]
action_scripts = ["myplugin.actions"]
event_listener_modules = ["myplugin.listeners"]
injectable_handler_params = { current_user = {}, instance_data = { scope = "ActionInstance" } }
```

`injectable_handler_params` maps injectable parameter names to their scope
availability. Scope names are `Plugin`, `Device`, `ActionInstance`, and
`ActionInstanceWithDevice`; an omitted scope defaults to `Plugin`, which is
available to every event. The scope controls which event models may provide a
parameter; resolver callables are registered separately in code. The built-in
`command_sender` injectable is registered by the SDK at `Plugin` scope.

```python
from streamdeck.models.configs import StreamDeckToolConfig

config = StreamDeckToolConfig()
actions = config.actions
listeners = config.event_listeners
event_models = config.event_models
```

The plugin directory must be importable before loading these settings; the CLI
adds it to `sys.path` first. `--plugin-dir` controls module imports only; it does
not select a configuration file or change the working directory. Start the
launcher in the directory containing the intended `pyproject.toml`. The TOML
source uses its default working-directory lookup with no parent search, so no
explicit `Path.cwd()` or file path is needed.

Explicit CLI action scripts take precedence over the TOML action list before
module imports and validation. Omitted action-script
arguments retain the TOML value. A missing file or section contributes no values;
CLI arguments may supply required settings, otherwise validation reports missing
fields. Unknown TOML settings remain ignored.

The host options `-port` (also `-p`), `-pluginUUID`, `-registerEvent`, and `-info`
are required. Development options remain `--plugin-dir`, repeated
`--action-scripts`, repeated `--event-listener` (also `--event-listener-modules`),
and `--debug` (also `-d`). Each supplied module list replaces its corresponding
TOML list independently; omitted lists retain TOML values. `--help` requires no
host arguments or TOML file. Generated double-dash host option names also work.
Help and parser errors use argparse formatting; model validation errors are
logged by the entry point before exiting with status 2. Typer's shell-completion
flags are removed.
JSON launch information must contain a string at `plugin.uuid`. The plugin
directory defaults to the working directory when parsing. Pydantic's
`DirectoryPath` requires it to exist and be a directory; it does not precheck
readability. Import-time permission failures surface when modules are loaded.

`LaunchArguments.info` is a nested `RegistrationInfo` model. Its `plugin_uuid`
field uses `AliasPath("plugin", "uuid")` to extract and validate the only launch
information used by the SDK. Access it as `launch.info.plugin_uuid`. Unknown
fields are ignored by the model; its dump, passed to the manager, contains the
flat `plugin_uuid` key.

`StreamDeckToolConfig.settings_customise_sources()` returns the filtered CLI
source first and the TOML source second. `_add_plugin_module_argument` registers
help and destinations `action_scripts` and `event_listener_modules`, adding
`--event-listener` as a shorter alias for `--event-listener-modules`.
`cli_kebab_case=True` preserves `--action-scripts`; `cli_ignore_unknown_args=True`
lets this narrow parser ignore host and development options handled by
`LaunchArguments`. The initial launch parser still rejects unknown options.

```python
config = StreamDeckToolConfig()
```

Omitted module options contribute no override, leaving their TOML lists
intact. For programmatic construction, `_cli_parse_args=[]` disables process
input for this construction; an explicit list can supply test arguments instead.

The installed `streamdeck` command invokes `streamdeck.__main__:main`.
`main(argv=None)` captures the argument list once and passes it explicitly to both
settings models. It prepares the module import path, logging, and optional
debugging before loading plugin settings, then calls `run_plugin(launch, config)`
to create the manager, register listeners before actions, and run it. The runtime
function does not parse arguments or load settings. `python -m streamdeck` uses
the same entry point. Startup and execution failures are logged and re-raised.

Process arguments are parsed twice: once for launch validation, then for the
plugin's restricted override. Plugin modules are imported only during the final
merged settings validation, after the launcher configures the module import path.
The settings model has no custom constructor or `ContextVar`. The earlier
`toml_file` and `action_scripts_override` parameters are removed.

`PyProjectConfigs`, `ToolSection`, and their forwarding properties have been
removed. Use `StreamDeckToolConfig` directly. Discovery lists are now derived
from each settings instance, fixing accumulation across repeated loads. The
`iter_module_objects` helper reads `vars(module).items()` in namespace insertion
order and skips names starting with `__`; it does not invoke dynamic attribute
discovery through `__dir__` or `__getattr__`. Discovery still includes imported
objects and does not deduplicate them.

All three discovery properties use `cached_property`. The listener and event-model
properties share a private cached tuple, `_event_listener_objects`, so their
modules are scanned once per configuration instance. Changing modules or module
lists after discovery does not refresh these caches; construct a new configuration
instance to rediscover objects. Event models still reach the manager through
registered listeners' `event_models`.

Regression coverage is in
[`test_toml_settings.py`](tests/models/test_toml_settings.py) and
[`test_launch_settings.py`](tests/test_launch_settings.py). These tests use
local modules and do not establish live Stream Deck integration.

PR CI runs Python 3.10–3.15 plus distribution-build and installed-wheel checks.
Passing those checks does not establish live Stream Deck startup. See the PR's
checks for results at a particular commit.
