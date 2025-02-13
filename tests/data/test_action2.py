from streamdeck.actions import Action
from streamdeck.models.events import ApplicationDidTerminate


test_action2 = Action("my-first-test-action")


@test_action2.on("applicationDidTerminate")
def handle_application_terminated_event(event_data: ApplicationDidTerminate) -> None:
    print("ApplicationDidTerminate event handled.")
