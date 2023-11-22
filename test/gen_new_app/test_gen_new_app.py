import os
import os.path as osp
import shutil
import sys
import tomllib
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


_paths = _create_paths()
# pytest will prepend first-encountered import paths to sys.path, which will be res/skeleton/src
imp = util.safe_import_module('imp', _paths.srcDir, reload=True)

# dst_root = ...
# _dst_paths = _create_paths(dst_root)


def setup_function():
    """
    - use the following pattern to create a clean workspace for each test case:
    # clean = osp.join(_paths.caseInitDir, 'data')
    # workspace = osp.join(_paths.caseWorkDir, 'data')
    # shutil.copytree(clean_data, workspace, dirs_exist_ok=True)
    """
    teardown_function()
    os.makedirs(_paths.caseWorkDir, exist_ok=True)
    pass


def teardown_function():
    """
    - use the following pattern to clean up workspace after each test case:
    # util.safe_remove(_paths.caseWorkDir)
    """
    util.safe_remove(_paths.caseWorkDir)
    pass


def test_new_app_generated_under_cwd():
    """
    - must update args in tests after changing CLI
    """
    sys.path.insert(0, _paths.srcDir)
    args = types.SimpleNamespace()
    args.appRoot = osp.join(_paths.caseWorkDir, 'hello')
    args.appTemplate = 'form'
    args.forceOverwrite = False
    core = imp.Core(args)
    core.run()
    proj_cfg = osp.abspath(f'{_paths.caseWorkDir}/hello/pyproject.toml')
    with open(proj_cfg, "rb") as f:
        data = tomllib.load(f)
    assert data['tool']['poetry']['name'] == 'hello'
