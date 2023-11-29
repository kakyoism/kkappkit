import os
# 3rd party
import kkpyutil as util
# project
import base


_build_var_map = {
    '$APPDATA$': util.get_platform_appdata_dir(),
    '$HOME$': util.get_platform_home_dir(),
    '$TEMP$': util.get_platform_tmp_dir(),
    '$CWD$': os.getcwd(),
    "$APP$": 'oscillator'
}


class Core(base.Core):
    """
    - implement business logic
    """
    def __init__(self, args, logger=None):
        super().__init__(args, logger)

    def validate_args(self, args):
        """
        - reimplement in subclass
        """
        self.args = super().validate_args(args)
        self.args.csoundScript = util.substitute_keywords(self.args.csoundScript, _build_var_map, useliteral=True)
        if not os.path.isfile(self.args.csoundScript):
            self.logger.warning(f'Missing user Csound script: {self.args.csoundScript}; will use default script')
            self.args.csoundScript = os.path.join(os.path.dirname(__file__), '../res/tonegen.csd')
        return self.args

    def main(self):
        cmd = ['csound', self.args.csoundScript, '-odac']
        util.run_daemon(cmd)
