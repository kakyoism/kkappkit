import threading
import time
# project
import kkpyui as ui
import impl


class ControllerImp:
    """
    - implement all gui event-handlers
    """
    def __init__(self, ctrlr, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.controller = ctrlr

    def on_submit(self, event=None):
        """
        - subclass this to implement custom logic
        """
        self.controller.update()
        # lambda wrapper ensures "self" is captured by threading as a context
        # otherwise ui thread still blocks
        threading.Thread(target=lambda: self.run_background(), daemon=True).start()

    def on_cancel(self, event=None):
        self.controller.on_quit()

    def run_background(self):
        """
        - override this in app
        - run in background thread to avoid blocking UI
        """
        self.controller.set_progress('/start', 0, 'Processing ...')
        for p in range(101):
            # Simulate a task
            time.sleep(0.01)
            self.controller.set_progress('/processing', p, f'Processing {p}%...')
        self.controller.set_progress('/stop', 100, 'Completed!')
        prompt = ui.Prompt()
        prompt.info('Finished. Will open result in default browser', confirm=True)
        core = impl.Core(self.controller.pack())
        core.main()

    def on_activate(self, event=None):
        pass

    def on_term(self, event=None):
        pass
