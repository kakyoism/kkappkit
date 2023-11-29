import glob
import os.path as osp
import sys
import tomllib
# 3rd-party
from cx_Freeze import setup, Executable
import kkpyutil as util


def load_proj_config(src_root):
    """
    - return a dict
    """
    return tomllib.load(open(osp.join(src_root, 'pyproject.toml'), 'rb'))


def load_dependencies(src_root):
    """
    - packages are defined as dependencies in pyproject.toml
    """
    dep_config = load_proj_config(src_root)['tool']['poetry']['dependencies']
    return list(dep_config.keys())


def load_dev_dependencies(src_root):
    dep_config = load_proj_config(src_root)['tool']['poetry']['dev-dependencies']
    return list(dep_config.keys())


def extend_import_path(src_root):
    """
    - add more folders if needed; it's recommended to place all sources flatly under src/
    """
    return sys.path + [osp.join(src_root, 'src')]


def plan_to_deploy_resources(src_root, dst_data_dir='lib'):
    """
    - add more files if needed
    - it's recommended to place all resources flatly under res/
    - cx_freeze asks for a list of (src, dst) pairs to copy data files
    - dst is relative to exe folder under build root
    """
    src_res_dir = osp.join(f'{src_root}/res')
    dst_res_dir = osp.join(dst_data_dir, 'res')
    srcs = glob.glob(osp.join(src_res_dir, '*'), recursive=True)
    dsts = [osp.join(dst_res_dir, osp.relpath(src, src_res_dir)) for src in srcs]
    return list(zip(srcs, dsts))


def get_cli_entry(src_root):
    return osp.join(src_root, 'src', 'cli.py')


def get_gui_entry(src_root):
    return osp.join(src_root, 'src', 'gui.py')


def load_app_name(src_root):
    """
    - return None if it's a console app
    """
    return load_proj_config(src_root)['name']


def load_app_version(src_root):
    return load_proj_config(src_root)['version']


def load_app_description(src_root):
    return load_proj_config(src_root)['description']


def get_build_options_exe(src_root):
    return {
        'packages': load_dependencies(src_root),
        'excludes': load_dev_dependencies(src_root),
        'path': extend_import_path(src_root),
        'include_files': plan_to_deploy_resources(src_root)
    }


def get_build_options_dmg(src_root):
    return {
        "volume_label": f'{load_app_name(src_root)}-{load_app_version(src_root)}',
        "applications_shortcut": True,
    }


#
# main
#
_dev_root = osp.abspath(f'{osp.dirname(__file__)}/..')
_dev_src_dir = osp.join(_dev_root, 'src')
_dst_datadir = 'lib'

executables = [
    Executable(get_gui_entry(_dev_root), base='Win32GUI' if sys.platform == 'win32' else None, target_name=load_app_name(_dev_root)),
    Executable(get_cli_entry(_dev_root), base=None, target_name=f'{load_app_name(_dev_root)}_cli'),
]

setup(
    name=load_app_name(_dev_root),
    version=load_app_version(_dev_root),
    description=load_app_description(_dev_root),
    options={
        'build_exe': get_build_options_exe(_dev_root),
        'bdist_dmg': get_build_options_dmg(_dev_root),
    },
    executables=executables,
)
