import os.path as osp
import shutil
import types

# 3rd party
import kkpyutil as util
import pytest


# project
def _create_paths(root=None):
    paths = types.SimpleNamespace()
    paths.root = root or osp.abspath(f'{osp.dirname(__file__)}/../..')
    paths.srcDir = osp.join(paths.root, 'src')
    paths.testDir = osp.join(paths.root, 'test')
    paths.testcaseDir = osp.dirname(__file__)
    paths.caseInitDir = osp.join(paths.testcaseDir, 'initial')
    paths.caseRefDir = osp.join(paths.testcaseDir, 'expected')
    paths.caseWorkDir = osp.join(paths.testcaseDir, 'observed')
    return paths


def _init_args(paths):
    app_config = util.load_json(paths.appCfg)
    app_input = app_config['input']
    defaults = {name: arg['default'] for name, arg in app_input.items()}
    return types.SimpleNamespace(**defaults)


_paths = _create_paths()
imp = util.safe_import_module('imp', _paths.srcDir)
# dst_root = ...
# _dst_paths = _create_paths(dst_root)


def setup_function():
    """
    - use the following pattern to create a clean workspace for each test case:
    # clean = osp.join(_paths.caseInitDir, data := 'hello')
    # workspace = osp.join(_paths.caseWorkDir, data)
    # shutil.copytree(clean, workspace, dirs_exist_ok=True)
    """
    pass


def teardown_function():
    """
    - use the following pattern to clean up workspace after each test case:
    # util.safe_remove(_paths.caseWorkDir)
    """
    pass


def test_default():
    """
    - must update args in tests after changing CLI
    """
    args = _init_args(_paths)
    #
    # CUSTOMIZE ARGS HERE
    #
    imp.Core(args).run()
    assert True
