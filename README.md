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

Use the `PluginManager` to run your plugin. It manages the WebSocket connection and dispatches events to your handlers.

```python
from streamdeck import PluginManager

# Replace these values with the ones provided by the Stream Deck software
PORT = 12345
PLUGIN_UUID = "your-plugin-uuid"
REGISTER_EVENT = "registerPlugin"
INFO = {}  # Additional info provided by the Stream Deck software

def main():
    plugin_manager = PluginManager(
        port=PORT,
        plugin_uuid=PLUGIN_UUID,
        register_event=REGISTER_EVENT,
        info=INFO
    )

    # Register your actions
    plugin_manager.register_action(my_action)

    # Run the plugin
    plugin_manager.run()

if __name__ == "__main__":
    main()
```

## Simple Example

Below is a complete example that creates a plugin with a single action. The action handles the `keyDown` event and sends a message back to the Stream Deck.

```python
from streamdeck import Action, PluginManager, events

# Define your action
my_action = Action(uuid="com.example.myaction")

# Register event handlers
@my_action.on("keyDown")
def handle_key_down(event):
    print("Key Down event received:", event)

# Set up and run the plugin
def main():
    parser = argparse.ArgumentParser(description="StreamDeck Plugin")
    parser.add_argument("-port", dest="port", type=int, help="Port", required=True)
    parser.add_argument("-pluginUUID", dest="pluginUUID", type=str, help="pluginUUID", required=True)
    parser.add_argument("-registerEvent", dest="registerEvent", type=str, help="registerEvent", required=True)
    parser.add_argument("-info", dest="info", type=str, help="info", required=True)
    args = parser.parse_args()

    plugin_manager = PluginManager(
        port=args.port,
        plugin_uuid=args.pluginUUID,
        register_event=args.registerEvent,
        info=args.info
    )

    plugin_manager.register_action(my_action)

    plugin_manager.run()

if __name__ == "__main__":
    main()
```


## Contributing

Contributions are welcome! Please open an issue or submit a pull request on GitHub. See the [development.md](development.md) for setting up and testing the project.


## Upcoming Improvements

The following upcoming improvements are in the works:

- **Improved Documentation**: Expand and improve the documentation with more examples, guides, and use cases.
- **Bind Command Sender**: Automatically bind `command_sender` and action instance context-holding objects to handler function arguments if they are included in the definition.
- **Optional Event Pattern Matching on Hooks**: Add support for optional pattern-matching on event messages to further filter when hooks get called.
- **CLI Entrypoint**: Add a command-line interface (CLI) entrypoint to the library to handle discovering actions, setting up, and running the `PluginManager`.
- **Async Support**: Introduce asynchronous features to handle WebSocket communication more efficiently.


## License

This project is licensed under the MIT License.

