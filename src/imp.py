import copy
import getpass
import os
import os.path as osp
import shutil
import types

# 3rd party
import kkpyutil as util

# project
import base


class Core(base.Core):
    def __init__(self, args, logger=None):
        super().__init__(args, logger)
        self.dstAppConfig = None

    def main(self):
        if is_new_app := self.args.appName:
            self._copy_skeleton()
        else:
            self._reset_interface()
        self._lazy_init_app_proj()
        self._generate_code()

    def _create_paths(self):
        self.paths = types.SimpleNamespace()
        self.paths.root = osp.abspath(f'{osp.dirname(__file__)}/../')
        self.paths.resDir = osp.join(self.paths.root, 'res')
        self.paths.skeletonDir = osp.join(self.paths.resDir, 'skeleton')
        self.paths.templateDir = osp.join(self.paths.resDir, 'template')

        app_root = os.getcwd()
        expected_app_cfg = osp.abspath(f'{app_root}/src/app.json')
        if is_new_app := not osp.isfile(expected_app_cfg):
            app_root = osp.join(os.getcwd(), self.args.appName)
            expected_app_cfg = osp.abspath(f'{app_root}/src/app.json')
        self.dstPaths = types.SimpleNamespace(
            root=app_root,
            srcDir=osp.join(app_root, 'src'),
            resDir=osp.join(app_root, 'res'),
            testDir=osp.join(app_root, 'test'),
            appCfg=expected_app_cfg,
            depCfg=osp.join(app_root, 'pyproject.toml'),
        )
        self.dstPaths.cli = osp.join(self.dstPaths.srcDir, 'cli.py')
        self.dstPaths.implementation = osp.join(self.dstPaths.srcDir, 'imp.py')
        self.dstPaths.output = osp.join(self.dstPaths.srcDir, 'output.py')
        self.dstPaths.gui = osp.join(self.dstPaths.srcDir, 'gui.py')

    def _validate_args(self, args):
        self.args = copy.deepcopy(args)
        app_root = os.getcwd()
        expected_app_cfg = osp.abspath(f'{app_root}/src/app.json')
        if gen_app_with_cfg := not self.args.appName:
            if not osp.isfile(expected_app_cfg):
                util.throw(FileNotFoundError, f'missing app-config under cwd: {expected_app_cfg}', 'retry creating new app with -n <app-name>')
        return self.args

    def _copy_skeleton(self):
        src = osp.join(self.paths.resDir, 'skeleton')
        dst = self.dstPaths.root
        shutil.copytree(src, dst, dirs_exist_ok=True)
        src = osp.abspath(f'{self.paths.templateDir}/{self.args.appTemplate}.app.json')
        dst = osp.abspath(f'{self.dstPaths.srcDir}/app.json')
        util.copy_file(src, dst)
        # because pytest forbids name clashing b/w test modules
        # skeleton test is named without test_ prefix to avoid name clashing with dst skeletion
        # after copying, we must prepend test_ back for pytest to collect the test normally
        src = osp.abspath(f'{self.dstPaths.testDir}/default/_default.py')
        dst = osp.abspath(f'{self.dstPaths.testDir}/default/test_default.py')
        os.rename(src, dst)

    def _lazy_init_app_proj(self):
        """
        - user gives app name only when creating new app
        """
        if to_update_app := not self.args.appName:
            # update toml
            return
        util.run_cmd(['poetry', 'init', '-n',
                      '--name', self.args.appName,
                      '--author', getpass.getuser(),
                      '--python', '^3.11',
                      '--dependency', 'kkpyutil',
                      '--dev-dependency', 'pytest',
                      ], cwd=self.dstPaths.root)
        # update app config
        self.appConfig = util.load_json(self.dstPaths.appCfg)
        self.appConfig['name'] = self.args.appName
        util.save_json(self.dstPaths.appCfg, self.appConfig)
        return True

    def _generate_code(self):
        self.appConfig = util.load_json(self.dstPaths.appCfg)
        # TODO: replace with json schema
        if is_new_app := not self.appConfig['name']:
            breakpoint()
            self.logger.warning('app.json is incomplete because its name is empty; complete app-config and rebuild the app')
            return
        # user has filled up app.json
        self._generate_cli()
        self._generate_out()
        self._generate_gui()

    def _generate_cli(self):
        code_lines = []
        for name, arg in self.appConfig['input'].items():
            codegen = ArgumentGen.create_codegen(name, arg)
            code_lines += codegen.generate().splitlines()
        code = '\n'.join(code_lines)
        # substitute template
        util.substitute_keywords_in_file(self.dstPaths.cli, {
            '{{name}}': self.appConfig['name'],
            '{{description}}': self.appConfig['description'],
            '{{tutorial}}': '\n'.join(self.appConfig['tutorial']),
            '{{remarks}}': '\n'.join(self.appConfig['remarks']),
            '# {{args}}': code,
        }, useliteral=True)



    def _generate_out(self):
        code_lines = [
            '#',
            '# GENERATED: DO NOT EDIT',
            '#',
            'output = {'
        ]
        indent = '    '
        data_lines = [f'{indent}\'{name}\': {repr(arg["default"])},' for name, arg in self.appConfig['output'].items()]
        code_lines += data_lines
        code_lines.append('}')
        util.save_lines(self.dstPaths.output, code_lines, addlineend=True)

    def _generate_gui(self):
        # code_lines = []
        # for name, arg in self.appConfig['input'].items():
        #     codegen = self._create_gui_codegen(name, arg)
        #     code_lines += codegen.generate()
        # # substitute template
        # code = '\n'.join(code_lines)
        pass

    def _reset_interface(self):
        for fn in ('cli.py', 'gui.py', 'out.py'):
            src = osp.abspath(f'{self.paths.skeletonDir}/src/{fn}')
            dst = osp.abspath(f'{self.dstPaths.srcDir}/{fn}')
            util.copy_file(src, dst)


class ArgumentGen:
    shortSwitches = set()

    def __init__(self, name, arg):
        self.name = name
        self.arg = arg
        self.shortSwitch = self._extract_short_switch()
        self.longSwitch = f'--{util.convert_compound_cases(self.name, style="kebab", instyle="snake")}'
        self.action = 'store'
        self.dest = util.convert_compound_cases(self.name, style="camel", instyle="snake")
        # for platform dependent defaults
        default = self.arg['default'][util.PLATFORM] if isinstance(self.arg['default'], dict) else self.arg['default']
        self.default = f"\'{default}\'" if self.arg['type'] == 'str' else default

    @staticmethod
    def create_codegen(name, arg):
        if arg['type'] == 'bool':
            return BoolGen(name, arg)
        if 'choices' in arg:
            return OptionGen(name, arg)
        if arg['type'] in ('int', 'float', 'str', 'list'):
            return ArgumentGen(name, arg)
        util.throw(ValueError, f'unknown argument type: {arg["type"]} for {name}', ['fix the type in app-config', 'support this type in code-gen'])

    def generate(self):
        """output code lines"""
        return util.indent(f"""\
parser.add_argument(
    {self.shortSwitch}
    '{self.longSwitch}',
    action='{self.action}',
    dest='{self.dest}',
    type={self.arg['type']},
    default={self.default},
    required={self.arg['required']},
    help='{self.arg['help']}'
)""")

    def _extract_short_switch(self):
        def _wrap_for_argparse_call(switch):
            return f'"{switch}",'

        # first unused initial of each part
        parts = self.name.split('_')
        initial_for_sw = next((part[0] for part in parts if part[0] not in ArgumentGen.shortSwitches), None)
        if initial_for_sw:
            ArgumentGen.shortSwitches.add(initial_for_sw)
            return _wrap_for_argparse_call(f'-{initial_for_sw}')
        cap_initial_for_sw = next((cpt for part in parts if (cpt := part[0].upper()) not in ArgumentGen.shortSwitches), None)
        if cap_initial_for_sw:
            ArgumentGen.shortSwitches.add(cap_initial_for_sw)
            return _wrap_for_argparse_call(f'-{cap_initial_for_sw}')
        # combine initials of 1st and 2nd part if applicable
        if has_multiparts := len(parts) > 1:
            concat_initials_for_sw = next((concat for p in range(len(parts) - 1) if (concat := f'{parts[p][0]}{parts[p + 1][0]}') not in ArgumentGen.shortSwitches), None)
            if concat_initials_for_sw:
                ArgumentGen.shortSwitches.add(concat_initials_for_sw)
                return _wrap_for_argparse_call(f'-{concat_initials_for_sw}')
            cap_concat_initials_for_sw = next((concat for p in range(len(parts) - 1) if (concat := f'{parts[p][0]}{parts[p + 1][0]}'.upper()) not in ArgumentGen.shortSwitches), None)
            if cap_concat_initials_for_sw:
                ArgumentGen.shortSwitches.add(cap_concat_initials_for_sw)
                return _wrap_for_argparse_call(f'-{cap_concat_initials_for_sw}')
        # give up
        return ''


class BoolGen(ArgumentGen):
    """
    parser.add_argument(
        '-e',
        '--enabled',
        action='store_true',
        dest='enabled',
        default=False,
        required=False,
        help=''
    )
    """

    def __init__(self, name, arg):
        super().__init__(name, arg)
        self.action = 'store_true' if not self.arg['default'] else 'store_false'

    def generate(self):
        return util.indent(f"""\
parser.add_argument(
    {self.shortSwitch}
    '{self.longSwitch}',
    action='{self.action}',
    dest='{self.dest}',
    default={self.arg['default']},
    required={self.arg['required']},
    help='{self.arg['help']}'
)""")


class ListGen(ArgumentGen):
    """
    parser.add_argument(
        '-l',
        '--my-int-list',
        action='store',
        nargs='*',
        dest='mylist',
        type=int,
        default=[],
        required=False,
        help=''
    )
    """

    def __init__(self, name, arg):
        super().__init__(name, arg)
        if allow_empty := self.arg['range'][0] == 0:
            self.nArgs = repr('+')
        elif fixed_count := self.arg['range'][0] == self.arg['range'][1] and isinstance(self.arg['range'][0], int):
            assert len(self.arg['default']) == self.arg['range'][0]
            self.nArgs = self.arg['range'][0]
        elif not_empty := self.arg['range'][0] > 0 and (self.arg['range'][1] is None or self.arg['range'][1] > 0):
            assert len(self.arg['default']) > 0
            self.nArgs = repr('+')

    def generate(self):
        return util.indent(f"""\
parser.add_argument(
    {self.shortSwitch}
    '{self.longSwitch}',
    action='{self.action}',
    nargs={self.nArgs},
    dest='{self.dest}',
    type={self.arg['type']},
    default={self.arg['default']},
    required={self.arg['required']},
    help='{self.arg['help']}'
)""")


class OptionGen(ArgumentGen):
    """
    parser.add_argument(
        '-s',
        '--single-option',
        action='store',
        choices=('en', 'zh', 'jp'),
        dest='singleOption',
        default='zh',
        type=str,
        required=False,
        help=''
    )
    parser.add_argument(
        '-m',
        '--multiple-options',
        action='store',
        nargs='+',
        choices=(1, 2, 3),
        type=int,
        dest='multiOptions',
        default=[1, 3],
        required=False,
        help=''
    )
    """

    def __init__(self, name, arg):
        super().__init__(name, arg)
        assert self.arg['range'][1] is None or self.arg['range'][1] > 0, f'invalid option range: {self.arg["range"]}'
        self.nArgs = 1 if self.arg['range'][1] == 1 else f"\'+\'"
        assert not isinstance(self.arg['default'], dict), 'expected option args to be consistent across platforms, but got platform-dependent defaults'
        self.default = f"\'{self.arg['default']}\'" if isinstance(self.arg['default'], str) else self.arg['default']

    def generate(self):
        return util.indent(f"""\
parser.add_argument(
    {self.shortSwitch}
    '{self.longSwitch}',
    action='{self.action}',
    nargs={self.nArgs},
    choices={self.arg['choices']},
    dest='{self.dest}',
    type={self.arg['type']},
    default={repr(self.arg['default'])},
    required={self.arg['required']},
    help='{self.arg['help']}'
)""")


#
# output
#
class OutputGen:
    def __init__(self, name, arg):
        self.name = name
        self.arg = arg

    def generate(self):
        return []


#
# gui
#
class FormEntryGen:
    def __init__(self, name, arg):
        self.name = name
        self.arg = arg

    def generate(self):
        return []
