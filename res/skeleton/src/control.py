"""
- implement callbacks on_*() defined in gui-controller prototype
"""
import kkpyui as ui
import impl


class Controller({{BASE_CONTROLLER}}):
    """
    """
    def __init__(self, ctrlr, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_open_help(self):
        """
        - implement this to open help URL/file in default browser
        """
        pass

    def on_open_log(self):
        """
        - implement this to open log file in default browser
        """
        pass

    def on_report_issue(self):
        """
        - implement this to receive user feedback
        """
        pass

    def on_startup(self):
        """
        - called just before showing root window, after all fields are initialized
        - so that fields can be used here for the first time
        """
        pass

    def on_shutdown(self, event=None) -> bool:
        """
        - called just before quitting
        - base-class safe-schedules shutdown with prompt and early-outs if user cancels
        - impelement post-user-confirm logic here, or override completely
        """
        if not super().on_shutdown():
            return False
        # IMPELEMENT POST-USER-CONFIRM LOGIC HERE
        return True

    def run_task(self):
        """
        - runs in a background thread out of the box to unblock UI
        - implement this to execute the main task in the background
        """
        {{REFLECT_OUTPUT}}
        pass

    def on_cancel(self, event=None):
        """
        - if task-thread is alive, base-controller schedules stop-event and waits for task to finish
        - implement pre-cancel and post-cancel logic here, or override completely
        """
        # IMPLEMENT PRE-CANCELLING LOGIC HERE, E.G., DATA PROTECTION
        super().on_cancel(event)
        # IMPLEMENT POST-CANCELLING LOGIC HERE, E.G., CLEANUP
