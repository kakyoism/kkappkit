import threading
import time
# project
import kkpyui as ui
import kkpyutil as util
import impl


class ControllerImp:
    """
    - implement all gui event-handlers
    """
    def __init__(self, ctrlr, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.controller = ctrlr
        self.core = impl.Core(self.controller.get_latest_model())

    def on_open_help(self):
        util.alert('Dev: Just use it! Trust yourself and the log!')

    def on_open_log(self):
        self.core.open_log()

    def on_report_issue(self):
        util.alert('Dev: It\'s not a bug, it\'s a feature!')

    def run_task(self):
        """
        - override this in app
        - run in background thread to avoid blocking UI
        """
        self.controller.start_progress()
        for p in range(101):
            # Simulate a task
            time.sleep(0.01)
            self.controller.set_progress('/processing', p, f'Processing {p}%...')
            if self.controller.scheduled_to_stop():
                self.controller.stop_progress()
                return
        self.controller.stop_progress()
        prompt = ui.Prompt()
        prompt.info('Finished. Will open result in default browser', confirm=True)
        self.core.args = self.controller.get_latest_model()
        self.core.main()
