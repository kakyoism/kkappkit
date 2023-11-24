import os.path as osp
# 3rd party
import kkpyutil as util
# project
import base


class Core(base.Core):
    """
    - implement business logic
    """
    def __init__(self, args, logger=None):
        super().__init__(args, logger)

    def validate_args(self, args):
        """
        - called by super()__init__()
        """
        fixed_args = super().validate_args(args)
        return fixed_args

    def main(self):
        export = osp.join(self.paths.sessionDir, 'out.json')
        util.save_json(export, vars(self.args))
        util.open_in_browser(export)
