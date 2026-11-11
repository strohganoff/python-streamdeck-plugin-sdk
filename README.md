# Python Stream Deck Plugin SDK

<p align="center">
    <em>Stream Deck SDK for Python plugins, easy to learn, fast to code</em>
</p>

---

A Python library for developing plugins for the Elgato Stream Deck. This library simplifies the process of creating Stream Deck plugins by providing classes and methods to handle WebSocket communication, event registration, and command sending.

This library differs from the official Stream Deck TypeScript SDK, as it aims to be more Pythonic, adhering to current Python conventions and trends. The goal is to make plugin development as simple and intuitive as possible for Python developers. Inspired by libraries like FastAPI, this project aims to provide a clear, concise, and developer-friendly experience for Python Stream Deck plugin development.


See the [configuration guide](CONFIGURATION.md) for launch arguments, settings
sources, and module discovery behavior.

## Features

- **WebSocket Abstraction**: WebSocket communication is abstracted away, so users don't need to handle WebSocket connections directly.

- **Event Hooks**: Users simply define actions and their hooks that get automatically routed and called every time the Stream Deck sends the appropriate event. No need to subclass abstract Action classes.

- **Event Models**: Events received from the Stream Deck are fully modeled and typed using Pydantic, allowing for validation and making them easier to work with and develop against.

- **PluginManager**: Orchestrates action lifecycle, event-routing, and context-gathering behind the scenes.

- **CLI Tool**: Quickly create new plugins projects from a template and package them to use on your Stream Deck using [the Python sdk cli tool](https://github.com/strohganoff/python-streamdeck-plugin-sdk-cli).

## Installation

You can install the library via pip:

```bash
pip install streamdeck-plugin-sdk
```

## Getting Started

This guide will help you set up your first Stream Deck plugin using the library.

### Prerequisites

- Python 3.10 or higher
- Stream Deck software installed
- A valid `manifest.json` file for your plugin

### Creating Actions

The SDK provides two types of actions: `Action` and `GlobalAction`. Each represents functionality with different scopes in your plugin, determining how  events are handled.

#### Regular Actions

An `Action` handles events that are specifically associated with it based on event metadata. When the Stream Deck sends an event, the action's handlers only run if the event metadata indicates it was triggered by or is intended for that specific action instance.

```python
from streamdeck.event_handlers.actions import Action

# Create an action with a unique UUID (from your manifest.json)
my_action = Action(uuid="com.example.myplugin.myaction")
```

#### Global Actions

A `GlobalAction` runs its event handlers for all events of a given type, regardless of which action the events were originally intended for. Unlike regular Actions which only process events specifically targeted at their UUID, GlobalActions handle events meant for any action in the plugin, making them useful for implementing plugin-wide behaviors or monitoring.

```python
from streamdeck.event_handlers.actions import GlobalAction

# Create a global action
my_global_action = GlobalAction()
```

Choose `GlobalAction` when you want to handle events at the plugin-scope (i.e. globally) without filtering by action, and `Action` when you need to process events specific to particular actions.

Note that an action with its UUID still needs to be defined in the manifest.json. Global Actions are an abstract component unique to this library — the global behavior is not how the Stream Deck software itself handles registering actions and publishing events.

### Registering Event Handlers

Use the `.on()` method to register event handlers for specific events.

```python
@my_action.on("keyDown")
def handle_key_down(event_data):
    print("Key Down event received:", event_data)

@my_action.on("willAppear")
def handle_will_appear(event_data):
    print("Will Appear event received:", event_data)
```

!!!INFO Handlers for action-specific events are dispatched only if the event is triggered by the associated action, ensuring isolation and predictability. For other types of events that are not associated with a specific action, handlers are dispatched without such restrictions.

A handler must have a required positional parameter named `event_data` first; the `.on()` decorator checks this when applied. At startup, before opening the WebSocket, the manager checks that any other required parameters have a stored injectable value. The SDK provides `command_sender`; plugins can define additional injected parameters in `pyproject.toml`. The SDK passes injectable values by keyword, so declare them as positional-or-keyword or keyword-only.

```python
from streamdeck.command_sender import StreamDeckCommandSender


@my_action.on("willAppear")
def handle_will_appear(event_data, command_sender: StreamDeckCommandSender):
    # Use command_sender to interact with Stream Deck
    command_sender.set_title(context=event_data.context, title="Hello!")
    command_sender.set_state(context=event_data.context, state=0)
```

The `command_sender` parameter is optional. If included in the handler's signature, the SDK automatically injects a `StreamDeckCommandSender` instance that can be used to send commands back to the Stream Deck (like setting titles, states, or images). Startup raises `TypeError` for signatures whose required parameters cannot be supplied by dispatch.

Custom injectable parameters name an importable resolver in `pyproject.toml`. The table key is the handler parameter name, and the resolver is called with the event data whenever a handler requests that parameter:

```toml
[tool.streamdeck.injectable_handler_params.api_client]
resolver = "my_plugin.dependencies.resolve_api_client"
scope = "Plugin"
```

```python
# my_plugin/dependencies.py
api_client = ApiClient()

def resolve_api_client(event_data):
    return api_client
```

The resolver can return a module-level instance or compute an event-specific value. `scope` defaults to `Plugin` when omitted.

The SDK also provides built-in context parameters: `plugin_context` is available to every handler; `device_context` is available when the event identifies a device; and `action_context` and `action_instance_context` are available when it identifies an action instance. Startup rejects a handler whose requested context is unavailable for one of its event types.



### Writing Logs

For convenience, a logger is configured with the same name as the last part of the Action's UUID, so you can simply call logging.getLogger(<name>) with the appropriate name to get the already-configured logger that writes to a rotating file. The log file is located in the Stream Deck user log directory.

When creating actions in your plugin, you can configure logging using the logger name that matches the last part of your Action's UUID. For example, consider the following code:

```python
import logging
from streamdeck.event_handlers.actions import Action

logger = logging.getLogger("myaction")

my_action = Action(uuid="com.example.mytestplugin.myaction")
```

Here, the logger name "myaction" matches the last part of the UUID passed in to instantiate the Action ("com.strohganoff.mytestplugin.myaction"). 

#### Configuring your own Loggers

Loggers can also be easily configured using provided utility functions, allowing for flexibility. If custom logging configurations are prefered over the automatic method shown above, you can use the following functions:

`configure_streamdeck_logger`: Configures a logger for the Stream Deck plugin with a rotating file handler that writes logs to a centralized location.

`configure_local_logger`: Configures a logger for a Stream Deck plugin that writes logs to a local data directory, allowing for plugin-specific logging.

These functions can be used to set up the logging behavior you desire, depending on whether you want the logs to be centralized or specific to each plugin.

For example:
```python
import logging
from streamdeck.utils.logging import configure_streamdeck_logger

configure_streamdeck_logger(name="myaction", plugin_uuid="com.example.mytestplugin")

logger = logging.getLogger("myaction")
```

Using the above code, you can ensure that logs from your action are properly collected and managed, helping you debug and monitor the behavior of your Stream Deck plugins.


### Running the Plugin

Once the plugin's actions and their handlers have been defined, very little else is needed to get this code running. With this library installed, the streamdeck CLI command   will handle the setup, loading of action scripts, and running of the plugin automatically, making it much easier to manage.

#### Usage

The commands below illustrate individual options. A real launch also requires all four Stream Deck launch arguments listed below.

The following commands are required, which are the same as the Stream Deck software passes in when running a plugin:

- `-port`: The port number assigned by the Stream Deck.

- `-pluginUUID`: The per-launch registration identifier provided by Stream Deck. The manifest plugin UUID comes from `-info` → `plugin.uuid`.

- `-registerEvent`: The event used to register your plugin. 

- `-info`: Additional information (formatted as json) about the plugin environment, as provided by the Stream Deck software.

    The SDK models this as `RegistrationInfo`, extracting the required string at `plugin.uuid` as `launch.info.plugin_uuid`. Other launch-info fields are ignored by this model. The manager receives the normalized dictionary `{"plugin_uuid": "..."}`.

The SDK uses Pydantic Settings to parse launch arguments and load `[tool.streamdeck]` from `pyproject.toml` in the current working directory, without searching parent directories. Constructing the `LaunchArguments` settings model parses and validates CLI arguments automatically, using only its customized CLI source. Explicit action modules override the configured list. If the file or section is absent, `--action-scripts` can supply the required action modules.

There are also development options for locating action and listener modules. The Stream Deck software does not pass these options.

- Plugin Directory: Pass the directory containing the plugin files using `--plugin-dir`:

    ```bash
    streamdeck --plugin-dir myplugin_dir/
    ```
    This adds the directory to Python's module import path. It defaults to the current working directory and must point to an existing directory. It does not change which TOML file is read or change the working directory.

- Action Scripts Directly: Alternatively, pass importable module names directly using the `--action-scripts` option:

    ```bash
    streamdeck --action-scripts actions1 --action-scripts actions2
    ```

    These modules replace the TOML `action_scripts` list. Omitting this option preserves TOML actions.

- Event Listener Modules: Pass importable module names with repeated `--event-listener` options (also available as `--event-listener-modules`):

    ```bash
    streamdeck --event-listener myplugin.listener_a --event-listener myplugin.listener_b
    ```

    These modules replace the TOML `event_listener_modules` list and are scanned for listener and event classes. Omitting the option preserves TOML listeners. The manager registers event models declared by each discovered listener's `event_models` attribute.

The plugin settings model's CLI source registers only action and listener module options, ignoring host arguments already checked by the launch parser. Environment variables, dotenv files, secrets, and constructor field values do not supply plugin settings.

Module discovery reads module namespace values in definition/import order, including imported objects. It skips names starting with `__` and does not deduplicate objects. Discovery results are cached per configuration instance; listener and event-model discovery share one cached collection. Changes to module contents or configured module lists after discovery do not refresh those results; create a new configuration instance to rediscover them.

Use `streamdeck --help` without launch arguments to see the available options. Help and argument errors use argparse formatting; Typer's shell-completion options are no longer available.

The CLI entry point `streamdeck.__main__.main(argv=None)` accepts an optional argument list, excluding the executable name. Both settings models use that same list; omitting it uses the process arguments. Startup prepares imports, logging, and optional debugging before loading plugin settings, then calls `run_plugin(launch, config)` with both validated models. Startup and runtime failures are logged and re-raised.

In addition to these, there is an additional option to use **debug mode**, which is discussed below.

#### Debugging

The SDK supports remote debugging capabilities, allowing you to attach a debugger after the plugin has started. This is particularly useful since Stream Deck plugins run as separate processes.

To enable debug mode, pass in the option `--debug {debug port number}`, which tells the plugin to wait for a debugger to attach on that port number.

```bash
streamdeck --debug 5675
```

Debug mode requires `debugpy` (included in the development extra). The plugin waits until a debugger attaches; there is no fixed timeout. You'll see a message in the logs indicating that the plugin is waiting for a debugger to attach.

NOTE: If things get messy, and you have a prior instance already listening to that port, you should kill the process with something like the following command:

```bash
kill $(lsof -t -i:$DEBUG_PORT)
```

#### Debugging with VS Code

1. Create a launch configuration in `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Attach to Stream Deck Plugin",
            "type": "debugpy",
            "request": "attach",
            "connect": {
                "host": "localhost",
                "port": 5675
            },
            "pathMappings": [
                {
                    "localRoot": "${workspaceFolder}",
                    "remoteRoot": "."
                }
            ],
            "justMyCode": false
        }
    ]
}
```

2. Start your plugin with debugging enabled
3. When you see the "waiting for debugger" message, use VS Code's Run and Debug view to attach using the configuration above
4. Set breakpoints and debug as normal


#### Configuration

To configure your plugin to use the streamdeck CLI, add a tool.streamdeck section to your pyproject.toml with a list variable for action_scripts that should contain importable module names for all the action scripts you want the plugin to load.

Below is an example of the pyproject.toml configuration and how to run the plugin:
```toml
# pyproject.toml

[tool.streamdeck]
    action_scripts = [
        "actions1",
        "actions2",
    ]
```

## Simple Example

Below is a complete example that creates a plugin with a single action. The action handles the `keyDown` and `applicationDidLaunch` event and simply prints a statement that an event occurred.

```python
# main.py
import logging
from streamdeck.event_handlers.actions import Action, GlobalAction
from streamdeck.models import events

logger = logging.getLogger("myaction")

# Define your action
my_action = Action(uuid="com.example.myplugin.myaction")

# Define your global action
my_global_action = GlobalAction()

# Register event handlers for regular action
@my_action.on("applicationDidLaunch")
def handle_application_did_launch(event_data: events.ApplicationDidLaunch):
    logger.debug("Application Did Launch event received: %s", event_data)

@my_action.on("keyDown")
def handle_key_down(event_data: events.KeyDown):
    logger.debug("Key Down event received: %s", event_data)

# Register event handlers for global action
@my_global_action.on("keyDown")
def handle_global_key_down(event_data: events.KeyDown):
    logger.debug("Global Key Down event received: %s", event_data)
```

```toml
# pyproject.toml
[tool.streamdeck]
    action_scripts = [
        "main",
    ]
```
And a command like the following is called by the Stream Deck software:
```bash
streamdeck -port 28196 -pluginUUID 63831042F4048F072B096732E0385245 -registerEvent registerPlugin -info '{"application": {...}, "plugin": {"uuid": "my-plugin-name", "version": "1.1.3"}, ...}'
```

## Custom Event Listeners

The SDK allows you to create custom event listeners and events by extending the `EventListener` and `EventBase` classes. This is useful when you need to monitor data from external applications and perform specific actions in response to changes or alerts.

### Creating a Custom Event Listener

To create a custom event listener:

1. Create new event model that inherits from `EventBase[Literal["eventName"]]`.
2. Create a new class that inherits from `EventListener`.
    a. Implement the required `listen` and `stop` methods. The `listen` method should yield results as a json string that matches the new event model.
    b. List the new event classes in the `event_models` class variable of the new `EventListener` class.
3. Configure your plugin in its `pyproject.toml` file to use your custom listener.

```python
# custom_listener.py
from collections.abc import Generator
from typing import ClassVar, Literal

from streamdeck.event_listener import EventListener
from streamdeck.models.events import EventBase


class MyCustomEvent(EventBase[Literal["somethingHappened"]]):
    # The 'event' field's type annotation is internally set as Literal["somethingHappened"]
    # Define additional data attributes here
    result: str


class MyCustomEventListener(EventListener):
    event_models = [MyCustomEvent]
    
    def listen(self) -> Generator[str | bytes, None, None]:
        ...
        # Listen/poll for something here in a loop, and yield the result.
        # This will be ran in a background thread.
        # Ex:
        # while self._running is True:
        #     result = module.check_status()
        #     if result is not None:
        #         yield json.dumps({"event": "somethingHappened", "result": result})
        #     time.sleep(1)

    def stop(self) -> None:
        ...
        # Stop the loop or blocking call in the listen method.
        # Ex:
        # self._running = False
```

### Configuring Your Custom Listener

To use your custom event listener, add it to your `pyproject.toml` file:

```toml
[tool.streamdeck]
    action_scripts = [
        "main",
    ]
    event_listener_modules = [
        "myplugin.custom_listener",
    ]
```

The `event_listener_modules` list should contain strings in module format for each module you want to use.


## Creating and Packaging Plugins

To create a new plugin with all of the necessary files to start from and package it for use on your Stream Deck, use [the Python SDK CLI tool](https://github.com/strohganoff/python-streamdeck-plugin-sdk-cli).

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on GitHub. See the [development.md](development.md) for setting up and testing the project.


## Upcoming Improvements

The following upcoming improvements are in the works:

- **Improved Documentation**: Expand and improve the documentation with more examples, guides, and use cases.
- **Store & Bind Settings**: Automatically store and bind action instance context-holding objects to handler function arguments if they are included in the definition.
- **Optional Event Pattern Matching on Hooks**: Add support for optional pattern-matching on event messages to further filter when hooks get called.
- **Async Support**: Introduce asynchronous features to handle WebSocket communication more efficiently.


## License

This project is licensed under the MIT License.

