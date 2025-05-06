from streamdeck.event_handlers.actions import Action, GlobalAction
from streamdeck.models.events import ApplicationDidLaunch


test_action2 = Action("my-first-test-action")

test_global_action1 = GlobalAction()


@test_action2.on("applicationDidLaunch")
def handle_application_launched_event(event_data: ApplicationDidLaunch) -> None:
    print("ApplicationDidLaunch event handled.")


@test_global_action1.on("applicationDidLaunch")
def handle_application_launched_event_globally(event_data: ApplicationDidLaunch) -> None:
    print("Global ApplicationDidLaunch event handled.")
