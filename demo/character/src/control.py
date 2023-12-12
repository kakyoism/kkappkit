import threading
import time
# project
import kkpyui as ui
import kkpyutil as util
import impl


class Controller(ui.FormController):
    """
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.core = impl.Core(args=None)

    def on_open_help(self):
        util.alert('Dev: Just use it! Trust yourself and the log!')

    def on_open_diagnostics(self):
        self.core.on_open_diagnostics()

    def on_report_issue(self):
        util.alert('Dev: It\'s not a bug, it\'s a feature!')

    def on_startup(self):
        """
        - called just before showing root window, after all fields are initialized
        - so that fields can be used here for the first time
        """
        print('Welcome!')

    def on_shutdown(self, event=None) -> bool:
        """
        - called just before quitting
        - base-class safe-schedules shutdown with prompt and early-outs if user cancels
        - impelement post-user-confirm logic here, or override completely
        """
        if not super().on_shutdown():
            return False
        print('bye!')
        return True

    def run_task(self):
        self.start_progress()
        for p in range(101):
            # Simulate a task
            time.sleep(0.01)
            self.set_progress('/processing', p, f'Processing {p}%...')
            if self.is_scheduled_to_stop():
                self.stop_progress()
                return
        self.stop_progress()
        prompt = ui.Prompt()
        prompt.info('Finished. Will open result in default browser', confirm=True)
        self.core.args = self.get_latest_model()
        self.core.main()
        # reflect output
        self.model['export'] = self.core.out.export
        self.update_view()

    def on_cancel(self, event=None):
        """
        - if task-thread is alive, base-controller schedules stop-event and waits for task to finish
        - implement pre-cancel and post-cancel logic here, or override completely
        """
        # IMPLEMENT PRE-CANCELLING LOGIC HERE, E.G., DATA PROTECTION
        super().on_cancel(event)
        # IMPLEMENT POST-CANCELLING LOGIC HERE, E.G., CLEANUP
