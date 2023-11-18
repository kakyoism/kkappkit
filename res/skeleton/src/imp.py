# 3rd party

# project
import base


class Core(base.Core):
    """
    - implement business logic
    """
    def __init__(self, args, logger=None):
        super().__init__(args, logger)

    def main(self):
        pass


class Controller:
    """
    - implement all gui event-handlers
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
