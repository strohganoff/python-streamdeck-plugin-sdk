from streamdeck.actions import Action
from streamdeck.command_sender import StreamDeckCommandSender
from streamdeck.models.events import KeyDown, WillAppear


test_action1 = Action("my-first-test-action")


@test_action1.on("keyDown")
def handle_key_down_event(event_data: KeyDown) -> None:
    print("KeyDown event handled.")


@test_action1.on("willAppear")
def handle_will_appear_event(event_data: WillAppear, command_sender: StreamDeckCommandSender) -> None:
    print("WillAppear event handled.", command_sender)
