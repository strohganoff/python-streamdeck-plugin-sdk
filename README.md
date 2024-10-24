# Python Stream Deck Plugin SDK

<p align="center">
    <em>Stream Deck SDK for Python plugins, easy to learn, fast to code</em>
</p>

---

A Python library for developing plugins for the Elgato Stream Deck. This library simplifies the process of creating Stream Deck plugins by providing classes and methods to handle WebSocket communication, event registration, and command sending.

This library differs from the official Stream Deck TypeScript SDK, as it aims to be more Pythonic, adhering to current Python conventions and trends. The goal is to make plugin development as simple and intuitive as possible for Python developers. Inspired by libraries like FastAPI, this project aims to provide a clear, concise, and developer-friendly experience for Python Stream Deck plugin development.


## Features

- **WebSocket Abstraction**: WebSocket communication is abstracted away, so users don't need to handle WebSocket connections directly.

- **Event Hooks**: Users simply define actions and their hooks that get automatically routed and called every time the Stream Deck sends the appropriate event. No need to subclass abstract Action classes.

- **Event Models**: Events received from the Stream Deck are fully modeled and typed using Pydantic, allowing for validation and making them easier to work with and develop against.

- **PluginManager**: Orchestrates action lifecycle, event-routing, and context-gathering behind the scenes.

## Installation

You can install the library via pip:

```bash
pip install streamdeck-plugin-sdk
```

## Getting Started

This guide will help you set up your first Stream Deck plugin using the library.

### Prerequisites

- Python 3.8 or higher
- Stream Deck software installed
- A valid `manifest.json` file for your plugin

### Creating an Action

An **Action** represents a specific functionality in your plugin. You can create multiple actions, each with its own set of event handlers.

```python
from streamdeck import Action

# Create an action with a unique UUID (from your manifest.json)
my_action = Action(uuid="com.example.myaction")
```

### Registering Event Handlers

Use the `.on()` method to register event handlers for specific events.

```python
@my_action.on("keyDown")
def handle_key_down(event):
    print("Key Down event received:", event)

@my_action.on("willAppear")
def handle_will_appear(event):
    print("Will Appear event received:", event)
```

### Running the Plugin

Once the plugin's actions and their handlers have been defined, very little else is needed to get this code running. With this library installed, the streamdeck CLI command   will handle the setup, loading of action scripts, and running of the plugin automatically, making it much easier to manage.

#### Usage

The following commands are required, which are the same as the Stream Deck software passes in when running a plugin:

- `-port`: The port number assigned by the Stream Deck.

- `-pluginUUID`: Your plugin's unique identifier, provided by the Stream Deck.

- `-registerEvent`: The event used to register your plugin. 

- `-info`: Additional information (formatted as json) about the plugin environment, as provided by the Stream Deck software.

There are also  two additional options for specifying action scripts to load. Note that you can't use both of these options together, and the Stream Deck software doesn't pass in these options.

- Plugin Directory: Pass the directory containing the plugin files as a positional argument:

    ```bash
    streamdeck myplugin_dir/
    ```
    This will read the pyproject.toml file inside the directory to locate the action scripts. If this is not passed in, then the library looks in the current working directory for a pyproject.toml file.

- Action Scripts Directly: Alternatively, pass the script paths directly using the `--action-scripts` option:

    ```bash
    streamdeck --action-scripts actions1.py actions2.py
    ```


#### Configuration

To configure your plugin to use the streamdeck CLI, add a tool.streamdeck section to your pyproject.toml with a list variable for action_scripts that should contain paths to all the action scripts you want the plugin to load.

Below is an example of the pyproject.toml configuration and how to run the plugin:
```toml
# pyproject.toml

[tools.streamdeck]
    action_scripts = [
        "actions1.py",
        "actions2.py",
    ]
```

## Simple Example

Below is a complete example that creates a plugin with a single action. The action handles the `keyDown` event and simply prints a statement that the event occurred.

```python
# main.py

from streamdeck import Action, PluginManager, events

# Define your action
my_action = Action(uuid="com.example.myaction")

# Register event handlers
@my_action.on("keyDown")
def handle_key_down(event):
    print("Key Down event received:", event)
```

```toml
# pyproject.toml

[tools.streamdeck]
    action_scripts = [
        "main.py",
    ]
```
And a command like the following is called by the Stream Deck software:
```bash
streamdeck -port 28196 -pluginUUID 63831042F4048F072B096732E0385245 -registerEvent registerPlugin -info '{"application": {...}, "plugin": {"uuid": "my-plugin-name", "version": "1.1.3"}, ...}'
```


## Contributing

Contributions are welcome! Please open an issue or submit a pull request on GitHub. See the [development.md](development.md) for setting up and testing the project.


## Upcoming Improvements

The following upcoming improvements are in the works:

- **Improved Documentation**: Expand and improve the documentation with more examples, guides, and use cases.
- **Bind Command Sender**: Automatically bind `command_sender` and action instance context-holding objects to handler function arguments if they are included in the definition.
- **Optional Event Pattern Matching on Hooks**: Add support for optional pattern-matching on event messages to further filter when hooks get called.
- **Async Support**: Introduce asynchronous features to handle WebSocket communication more efficiently.


## License

This project is licensed under the MIT License.

