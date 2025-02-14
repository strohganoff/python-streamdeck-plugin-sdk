from streamdeck.actions import Action
from streamdeck.models.events import ApplicationDidLaunch


test_action2 = Action("my-first-test-action")


@test_action2.on("applicationDidLaunch")
def handle_application_launched_event(event_data: ApplicationDidLaunch) -> None:
    print("ApplicationDidLaunch event handled.")
