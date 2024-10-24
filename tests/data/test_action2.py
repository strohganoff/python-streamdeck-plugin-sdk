from streamdeck.actions import Action
from streamdeck.models.events import ApplicationDidTerminateEvent


test_action2 = Action("my-first-test-action")


@test_action2.on("applicationDidTerminate")
def handle_application_terminated_event(event_data: ApplicationDidTerminateEvent) -> None:
    print("ApplicationDidTerminate event handled.")
