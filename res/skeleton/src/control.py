"""
- implement callbacks on_*() defined in gui-controller prototype
"""
import kkpyui as ui
import impl


class ControllerImp:
    """
    """
    def __init__(self, ctrlr, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.controller = ctrlr

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
