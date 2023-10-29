import datetime
import getpass
import json
import os
import os.path as osp
import traceback
import types

# 3rd party
import toml
import kkpyutil as util


class Core:
    def __init__(self, args):
        self.args = args
        name = toml.load(osp.join(osp.dirname(__file__), 'pyproject.toml'))['tool']['poetry']['name']
        tmp_dir = osp.join(util.get_platform_tmp_dir(), name)
        session_dir = osp.join(tmp_dir, datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
        self.logger = util.build_default_logger(session_dir, name=name, verbose=True)
        self.root = osp.abspath(f'{osp.dirname(__file__)}/../')
        self.appPaths = None
        self.appConfig = None

    def main(self):
        self._validate_args()
        self._create_subdirs()
        self._lazy_init_app_proj()
        self._generate_code()

    def _validate_args(self):
        app_root = os.getcwd()
        expected_app_cfg = osp.abspath(f'{app_root}/src/app.json')
        if gen_app_with_cfg := not self.args.appName:
            if not osp.isfile(expected_app_cfg):
                util.throw(FileNotFoundError, f'missing app-config under cwd: {expected_app_cfg}', 'retry creating new app with -n <app-name>')
            # valid existing app
            self.appPaths = types.SimpleNamespace(
                root=app_root,
                srcDir=osp.abspath(f'{app_root}/src'),
                appCfg=expected_app_cfg,
                depCfg=osp.abspath(f'{app_root}/pyproject.toml'),
            )
            return
        # new app
        self.appPaths = types.SimpleNamespace(
            root=osp.join(os.getcwd(), self.args.appName),
        )
        self.appPaths.srcDir = osp.join(self.appPaths.root, 'src')
        self.appPaths.appCfg = osp.join(self.appPaths.srcDir, 'app.json')
        self.appPaths.depCfg = osp.join(self.appPaths.root, 'pyproject.toml')

    def _create_subdirs(self):
        for sub in (
                'ci',
                'res'
                'src',
                'test/default'
        ):
            osp.abspath(f'{self.args.parDir}/{self.args.name}/{sub}')
            self.logger.info(f'Create: {sub}')
            os.makedirs(sub, exist_ok=True)

    def _lazy_init_app_proj(self):
        if not self.args.appName:
            return
        util.run_cmd(['poetry', 'init', '-n'], cwd=self.appPaths.root)
        proj_config = toml.load('pyproject.toml')
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
            osp.abspath(f'{self.appPaths.root}/src/app.json')
        )
        for src, dst in zip(src_files, dst_files):
            util.copy_file(src, dst, isdstdir=True)

    def _generate_code(self):
        self.appConfig = util.load_json(self.appPaths.appCfg)
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
        pass

    def _create_out_codegen(self, arg):
        pass

    def _create_gui_codegen(self, arg):
        pass

