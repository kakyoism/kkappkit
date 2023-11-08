import copy
import types
# 3rd party
import kkpyutil as util
import os.path as osp
# project
import out


class Core:
    """
    - retrieve package name from pyproject.toml during dev and from pardir name on user-land
      - pyproject.toml cannot be shipped with the package because it's not part of a venv
      - build-pipeline cannot be restored at user-land
        - local repo name is unreliable due to git-clone renaming
    - no need to consider caller session because caller must import pacakge instead of subprocess
    """
    def __init__(self, args, logger=None):
        self.args = self._validate_args(args)
        self.out = out.Output()
        pkg_name = util.load_ini(osp.join(osp.dirname(__file__), 'pyproject.toml'))['tool.poetry']['name'] if self.is_dev_environment() else osp.basename(osp.dirname(__file__))
        tmp_dir = osp.join(util.get_platform_tmp_dir(), pkg_name)
        session_dir = osp.join(tmp_dir, util.format_now())
        self.logger = logger or util.build_default_logger(session_dir, name=pkg_name, verbose=True)
        self.paths = types.SimpleNamespace()
        self.paths.sessionDir = session_dir
        self._create_paths()

    @staticmethod
    def is_dev_environment():
        return osp.dirname(__file__) == 'src'

    def run(self):
        """
        - throw exception on error
        - return self.out on success
        """
        self.main()
        return self.out

    def _create_paths(self):
        pass

    def _validate_args(self, args):
        """
        - reimplement in subclass
        """
        self.args = copy.deepcopy(args)
        # IMPLEMENT VALIDATION HERE
        return self.args

    def main(self):
        raise NotImplementedError('implement in subclass')
