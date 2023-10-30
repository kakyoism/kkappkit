import copy
import datetime
import getpass
import glob
import json
import os
import os.path as osp
import traceback
import types

# 3rd party
import tomllib as toml
import kkpyutil as util

# project
import base


class Core(base.Core):
    def __init__(self, args, logger=None):
        super().__init__(args, logger)
        self.root = osp.abspath(f'{osp.dirname(__file__)}/../')
        self.dstPaths = None
        self.dstAppConfig = None

    def main(self):
        self._copy_skeleton()
        self._lazy_init_app_proj()
        self._generate_code()

    def _create_paths(self):
        self.paths = types.SimpleNamespace()
        self.paths.root = self.root,
        self.paths.resDir = osp.join(self.root, 'res')
        self.paths.skeletonDir = osp.join(self.paths.resDir, 'skeleton')
        self.paths.templateDir = osp.join(self.paths.resDir, 'template')

        app_root = os.getcwd()
        expected_app_cfg = osp.abspath(f'{app_root}/src/app.json')
        if is_new_app := not osp.isfile(expected_app_cfg):
            app_root = osp.join(os.getcwd(), self.args.appName)
        self.dstPaths = types.SimpleNamespace(
            root=app_root,
            srcDir=osp.join(app_root, 'src'),
            appCfg=expected_app_cfg,
            depCfg=osp.join(app_root, 'pyproject.toml'),
        )

    def _validate_args(self, args):
        self.args = copy.deepcopy(args)
        app_root = os.getcwd()
        expected_app_cfg = osp.abspath(f'{app_root}/src/app.json')
        if gen_app_with_cfg := not self.args.appName:
            if not osp.isfile(expected_app_cfg):
                util.throw(FileNotFoundError, f'missing app-config under cwd: {expected_app_cfg}', 'retry creating new app with -n <app-name>')
        return self.args

    def _copy_skeleton(self):
        src_files = glob.glob(osp.abspath(f'{self.root}/res/skeleton/*'), recursive=True)
        for src in src_files:
            dst = osp.join(self.dstPaths.root, osp.relpath(src, self.paths.skeletonDir))
            util.copy_file(src, dst, isdstdir=False)
            self.logger.debug(f'copied: {src} -> {dst}')

    def _lazy_init_app_proj(self):
        if not self.args.appName:
            return
        util.run_cmd(['poetry', 'init', '-n'], cwd=self.paths.root)
        with open(self.paths.depCfg, 'rb') as fp:
            proj_config = toml.load(fp)
        proj_config['tool']['poetry']['name'] = self.args.appName
        proj_config['tool']['poetry']['authors'] = [getpass.getuser()]
        self._init_source_files()
        return True

    def _init_source_files(self):
        src_files = [osp.abspath(f'{self.root}/src/template/{fn}') for fn in (
            'default.app.json',
            'cli.py',
            'out.py',
            'imp.py',
            'gui.py',
        )]
        dst_files = (
            osp.abspath(f'{self.paths.root}/src/app.json')
        )
        for src, dst in zip(src_files, dst_files):
            util.copy_file(src, dst, isdstdir=True)

    def _generate_code(self):
        self.appConfig = util.load_json(self.paths.appCfg)
        # TODO: replace with json schema
        if is_new_app := not self.appConfig['name']:
            util.throw(ValueError, 'app.json is incomplete because its name is empty', 'complete app-config and rebuild the app')
        # user has filled up app.json
        self._generate_cli()
        self._generate_out()
        self._generate_gui()

    def _generate_cli(self):
        code_lines = []
        for arg in self.appConfig['input']:
            codegen = self._create_cli_codegen(arg)
            code_lines += codegen.generate()
        # substitute template
        code = '\n'.join(code_lines)

    def _generate_out(self):
        code_lines = []
        for arg in self.appConfig['output']:
            codegen = self._create_out_codegen(arg)
            code_lines += codegen.generate()
        # substitute template
        code = '\n'.join(code_lines)

    def _generate_gui(self):
        code_lines = []
        for arg in self.appConfig['input']:
            codegen = self._create_gui_codegen(arg)
            code_lines += codegen.generate()
        # substitute template
        code = '\n'.join(code_lines)

    def _create_cli_codegen(self, arg):
        return None

    def _create_out_codegen(self, arg):
        return None

    def _create_gui_codegen(self, arg):
        return None

