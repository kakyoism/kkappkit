"""
- implement callbacks on_*() defined in gui-controller prototype
"""
import kkpyui as ui
import impl


class ControllerImp:
    """
    - implement all gui event-handlers
    """
    def __init__(self, ctrlr, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.controller = ctrlr
