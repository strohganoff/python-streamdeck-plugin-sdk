from streamdeck.actions import Action
from streamdeck.models.events import KeyDownEvent


test_action1 = Action("my-first-test-action")


@test_action1.on("keyDown")
def handle_key_down_event(event_data: KeyDownEvent) -> None:
    print("KeyDown event handled.")
