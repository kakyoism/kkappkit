import copy
import getpass
import glob
import os
import os.path as osp
import shutil
import types

# 3rd party
import kkpyutil as util

# project
import base

_build_var_map = {
    '$APPDATA$': 'util.get_platform_appdata_dir()',
    '$HOME$': 'util.get_platform_home_dir()',
    '$TEMP$': 'util.get_platform_tmp_dir()',
    '$CWD$': 'os.getcwd()',
    "$APP$": None
}


class Core(base.Core):
    def __init__(self, args, logger=None):
        super().__init__(args, logger)
        self.dstAppConfig = None

    def main(self):
        if is_new_app := self.args.forceOverwrite or not osp.isdir(self.args.appRoot):
            self._copy_skeleton()
        else:
            self._reset_interface()
        self._lazy_init_manifests()
        if self.args.impRoot:
            # app-config is part of the implementation
            # so it must be copied over before generating the interface
            self._update_app_config()
        self._generate_interface()
        if self.args.impRoot:
            # app-config is part of the implementation
            # so it must be copied over before generating the interface
            self._update_implementation()

    def _create_paths(self):
        self.paths = types.SimpleNamespace()
        self.paths.root = osp.abspath(f'{osp.dirname(__file__)}/../')
        self.paths.resDir = osp.join(self.paths.root, 'res')
        self.paths.skeletonDir = osp.join(self.paths.resDir, 'skeleton')
        self.paths.templateDir = osp.join(self.paths.resDir, 'template')

        expected_app_cfg = osp.abspath(f'{self.args.appRoot}/src/app.json')
        self.dstPaths = types.SimpleNamespace(
            root=self.args.appRoot,
            srcDir=osp.join(self.args.appRoot, 'src'),
            resDir=osp.join(self.args.appRoot, 'res'),
            testDir=osp.join(self.args.appRoot, 'test'),
            appCfg=expected_app_cfg,
            depCfg=osp.join(self.args.appRoot, 'pyproject.toml'),
        )
        self.dstPaths.cli = osp.join(self.dstPaths.srcDir, 'cli.py')
        self.dstPaths.imp = osp.join(self.dstPaths.srcDir, 'impl.py')
        self.dstPaths.output = osp.join(self.dstPaths.srcDir, 'out.py')
        self.dstPaths.gui = osp.join(self.dstPaths.srcDir, 'gui.py')
        self.dstPaths.ctrl = osp.join(self.dstPaths.srcDir, 'control.py')
        self.dstPaths.icon = osp.join(self.dstPaths.resDir, 'icon.png')

    def _validate_args(self, args):
        _args = copy.deepcopy(args)
        # because scripts are run by poetry, cwd is kkappkit root,
        # so we must use an absolute path for appRoot
        if not osp.isabs(_args.appRoot):
            util.throw(ValueError, f'Expected absolute path, received relative path: {_args.appRoot}', ['use absolute path for app root'])
        if _args.impRoot and not osp.isabs(_args.impRoot):
            util.throw(ValueError, f'Expected absolute path, received relative path: {_args.impRoot}', ['use absolute path for implementation root'])
        if _args.impRoot and not osp.isdir(_args.impRoot):
            util.throw(FileNotFoundError, f'Missing implementation root folder: {_args.impRoot}', ['Ensure path exists and spelling is correct'])
        if osp.isdir(_args.impRoot) and not osp.isfile(app_cfg := osp.abspath(f'{_args.impRoot}/src/app.json')):
            util.throw(FileNotFoundError, f'Missing app.json implementation: {app_cfg}, and so cannot generate interface', ['Ensure path exists and spelling is correct'])
        return _args

    def _copy_skeleton(self):
        util.backup_file(self.dstPaths.ctrl, dstdir=osp.join(self.dstPaths.srcDir, 'backup'))
        util.backup_file(self.dstPaths.imp, dstdir=osp.join(self.dstPaths.srcDir, 'backup'))
        src = osp.join(self.paths.resDir, 'skeleton')
        dst = self.dstPaths.root
        shutil.copytree(src, dst, dirs_exist_ok=True)
        src = osp.abspath(f'{self.paths.templateDir}/{self.args.appTemplate}.app.json')
        dst = osp.abspath(f'{self.dstPaths.srcDir}/app.json')
        util.copy_file(src, dst)
        # because pytest forbids name clashing b/w test modules
        # skeleton test is named without prefixing with test_ to avoid name clashing with dst skeleton
        # after copying, we must prepend test_ back for pytest to collect the test normally
        src = osp.abspath(f'{self.dstPaths.testDir}/default/_default.py')
        dst = osp.abspath(f'{self.dstPaths.testDir}/default/test_default.py')
        os.rename(src, dst)

    def _lazy_init_manifests(self):
        """
        - user gives app name only when creating a new app
        """
        app_name = osp.basename(self.args.appRoot)
        _build_var_map['$APP$'] = app_name
        if to_update_app := not self.args.forceOverwrite and osp.isfile(self.dstPaths.depCfg):
            # update toml
            return
        util.safe_remove(self.dstPaths.depCfg)
        util.run_cmd(['poetry', 'init', '-n',
                      '--name', app_name,
                      '--author', getpass.getuser(),
                      '--python', '^3.11',
                      '--dependency', 'kkpyutil',
                      '--dependency', 'kkpyui',
                      '--dev-dependency', 'pytest',
                      '--dev-dependency', 'coverage',
                      '--dev-dependency', 'cx_freeze',
                      '--dev-dependency', 'kkbuild',
                      ], cwd=self.dstPaths.root)
        # update app config
        self.appConfig = util.load_json(self.dstPaths.appCfg)
        self.appConfig['name'] = app_name
        util.save_json(self.dstPaths.appCfg, self.appConfig)
        # initialize venv and install dependency
        util.safe_remove(osp.join(self.dstPaths.root, 'poetry.lock'))
        util.run_cmd(['poetry', 'install'], cwd=self.dstPaths.root)
        return True

    def _generate_interface(self):
        self.appConfig = util.load_json(self.dstPaths.appCfg)

        # TODO: replace with json schema
        if is_new_app := not self.appConfig['name']:
            self.logger.warning('app.json is incomplete because its name is empty; complete app-config and rebuild the app')
            return
        # user has filled up app.json
        self._generate_cli()
        self._generate_out()
        self._generate_gui()

    def _update_app_config(self):
        appcfg_imp = osp.abspath(f'{self.args.impRoot}/src/app.json')
        util.copy_file(appcfg_imp, self.dstPaths.appCfg)

    def _update_implementation(self):
        """
        - if user provides implementation root, it's recommended to always edit the source code there
        - and let the codegen to directly overwrite the dst implementation
        """
        srcs = [file for file in util.collect_file_tree(self.args.impRoot) if osp.isfile(file)]
        dsts = [osp.join(self.dstPaths.root, osp.relpath(src, self.args.impRoot)) for src in srcs]
        for src, dst in zip(srcs, dsts):
            util.copy_file(src, dst)
        util.run_cmd(['poetry', 'install'], cwd=self.dstPaths.root)

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
        """
        - generate output code, e.g.:
          - output.myProp: myType = myValue
        - must add import by hand for custom types
        """
        indent = ' ' * 4
        raw_py_map = {
            'file': 'str',
            'folder': 'str',
            'path': 'str',
        }
        prop_assignment_lines = [f"{indent}{util.convert_compound_cases(name, style='camel')}: {raw_py_map.get(arg['type'], arg['type'])} = {repr(arg['default'])}" for name, arg in self.appConfig['output'].items()]
        code = '\n'.join(prop_assignment_lines)
        util.substitute_keywords_in_file(self.dstPaths.output, {'# {{assign}}': code}, useliteral=True)

    def _generate_gui(self):
        """
        - due to tkinter threading issue, progressbar and actionbar would be reversed against packing order,
        - to give user a consistent control, we pre-swap them to allow progressbar to update in the background and keep the action bar at the bottom
        """
        # main
        view_lines = util.indent(self._create_root() + self._create_form() + self._create_controller() + self._create_menu() + self._create_entries() + self._create_action() + self._create_progress() + self._create_mainloop())
        view_code = '\n'.join(view_lines)
        util.substitute_keywords_in_file(self.dstPaths.gui, {
            '# {{view}}': view_code,
        }, useliteral=True)
        # controller
        if ctrlr_api_changed := self.args.forceOverwrite:
            util.copy_file(osp.abspath(f'{self.paths.skeletonDir}/src/control.py'), self.dstPaths.ctrl)
        ctrlr_lines = ControllerGen.create_codegen(self.appConfig, self.dstPaths.ctrl).generate()
        util.save_lines(self.dstPaths.ctrl, ctrlr_lines, addlineend=True)


    def _reset_interface(self):
        for fn in ('cli.py', 'gui.py', 'out.py'):
            src = osp.abspath(f'{self.paths.skeletonDir}/src/{fn}')
            dst = osp.abspath(f'{self.dstPaths.srcDir}/{fn}')
            util.copy_file(src, dst)

    def _create_root(self):
        title = self.appConfig['appearance']['title']
        width = self.appConfig['appearance']['size'][0]
        height = self.appConfig['appearance']['size'][1]
        icon_file = self.dstPaths.icon
        icon = f'osp.abspath(f"{{osp.dirname(__file__)}}/../res/icon.png")' if osp.isfile(icon_file) else ''
        return [f"ui.Globals.root = ui.Root('{title}', ({width}, {height}), {icon})"]

    def _create_form(self):
        """
        - group is a gui-only tag
        - so we don't add group-layer to avoid confusing CLI roles
        - instead, use extra space for per-field group tag
        - group title uses title-casing without underscores
        """
        groups_with_dups = [util.convert_compound_cases(arg['group'], style='title') for name, arg in self.appConfig['input'].items()]
        groups = util.remove_duplication(groups_with_dups)
        groups.append('output')
        return [f'form = ui.Form(ui.Globals.root, page_titles={repr(groups)})']

    def _create_controller(self):
        return [
            'ctrlr = ctrl.Controller(form)',
            'ui.Globals.root.set_controller(ctrlr)',
            'ui.Globals.root.bind_events()',
        ]

    @staticmethod
    def _create_menu():
        return ['menu = ui.FormMenu(ui.Globals.root, ctrlr)']

    def _create_entries(self):
        """
        - in app-config, entries are defined in layout order
        - their groups are also sorted by layout order
        """
        groups = {arg['group'] for name, arg in self.appConfig['input'].items()}.union({'output'})
        pg_line_map = {grp: f"pg_{grp} = form.pages['{grp}']" for grp in groups}
        pgvar_lines = list(pg_line_map.values())
        entry_lines = [line for name, arg in self.appConfig['input'].items()
                       for line in EntryGen.create_codegen(name, arg).generate()]
        traceable_args = {name: arg for name, arg in self.appConfig['input'].items() if arg.get('trace')}
        tracer_lines = [f'{name.lower()}.set_tracer(ctrlr.on_{name.lower()}_changed)' for name, arg in traceable_args.items()]
        output_lines = [line for name, arg in self.appConfig['output'].items()
                       for line in OutputEntryGen.create_codegen(name, arg).generate()]
        return pgvar_lines + entry_lines + tracer_lines + output_lines

    def _create_action(self):
        template_cls_map = {
            'form': 'FormActionBar',
            'onoff': 'FormActionBar',
            'custom': 'ctrl.ActionBar',
        }
        return [f'action_bar = ui.{template_cls_map[self.appConfig["template"]]}(ui.Globals.root, ctrlr)']

    def _create_progress(self):
        template_cls_map = {
            'form': 'ProgressBar',
            'onoff': 'WaitBar',
        }
        # custom progressbar must be
        prog_type = self.appConfig['template']
        if not template_cls_map.get(prog_type):
            return []
        return [
            f'progress_bar = ui.{template_cls_map[prog_type]}(ui.Globals.root, ui.Globals.progressQueue)',
            'progress_bar.poll()',
        ]

    @staticmethod
    def _create_mainloop():
        return ['ui.Globals.root.mainloop()']


class ArgumentGen:
    shortSwitches = set('-h')

    def __init__(self, name, arg):
        self.name = name
        self.arg = arg
        self.shortSwitch = self._extract_short_switch()
        self.longSwitch = f'--{util.convert_compound_cases(self.name, style="kebab")}'
        self.action = 'store'
        self.dest = util.convert_compound_cases(self.name, style="camel")
        # for platform dependent defaults
        default = self.arg['default'][util.PLATFORM] if isinstance(self.arg['default'], dict) else self.arg['default']
        self.default = f"\'{default}\'" if isinstance(default, str) else default
        self.arg['required'] = self.arg['default'] is None

    @staticmethod
    def create_codegen(name, arg):
        """
        - order-sensitive code because some data types satisfy 2+ conditions
        - we ensure key-differentiator is the 1st condition
        - default is none/null for required args, must infer from default or obtain from type field
        """
        if isinstance(arg['default'], bool):
            arg['type'] = 'bool'
            return BoolArgGen(name, arg)
        if arg.get('choices') is not None:
            if not arg['choices'] and arg.get('type') is None:
                util.throw(ValueError, f"Expected option argument to provide choices and type hint, got: choices={arg['choices']}, type={arg.get('type')}", ['provide type field for empty choices', 'provide concrete choices for empty type hint'])
            if arg.get('type') is None:
                arg['type'] = type(arg['choices'][0]).__name__
                assert arg['type']
            return OptionArgGen(name, arg)
        if is_path := arg.get('type') in ('file', 'folder'):
            return PathArgGen(name, arg)
        if is_float := arg.get('precision'):
            arg['type'] = 'float'
            return FloatArgGen(name, arg)
        if is_int := arg.get('step') and not arg.get('precision'):
            arg['type'] = 'int'
            return IntArgGen(name, arg)
        if not_required_arg := isinstance(arg['default'], (int, str, list)):
            arg['type'] = type(arg['default']).__name__
            return ArgumentGen(name, arg)
        if is_required_arg := arg['default'] is None and isinstance(arg.get('type'), (int, str, list)):
            return ArgumentGen(name, arg)
        util.throw(ValueError, f'unknown argument type: {arg["type"]} for {name}', ['Option requires "choices" field', 'Float requires "precision" field', 'must provide type hint if default is None', 'fix the type in app-config',
                                                                                    'support this type in code-gen'])

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
    required={self.arg['default'] is None},
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


class BoolArgGen(ArgumentGen):
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


class ListArgGen(ArgumentGen):
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


class IntArgGen(ArgumentGen):
    def __init__(self, name, arg):
        super().__init__(name, arg)
        rg_min = "float('-inf')" if self.arg['range'][0] is None else int(self.arg['range'][0])
        rg_max = "float('inf')" if self.arg['range'][1] is None else int(self.arg['range'][1])
        self.range = f'({rg_min}, {rg_max})'

    def generate(self):
        return util.indent(f"""\
parser.add_argument(
    {self.shortSwitch}
    '{self.longSwitch}',
    action='{self.action}',
    dest='{self.dest}',
    type=ranged_{self.arg['type']}{self.range},
    default={self.arg['default']},
    required={self.arg['required']},
    help='{self.arg['help']}'
)""")


class FloatArgGen(IntArgGen):
    def __init__(self, name, arg):
        super().__init__(name, arg)
        rg_min = "float('-inf')" if self.arg['range'][0] is None else float(self.arg['range'][0])
        rg_max = "float('inf')" if self.arg['range'][1] is None else float(self.arg['range'][1])
        self.range = f'({rg_min}, {rg_max})'


class OptionArgGen(ArgumentGen):
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
        # option is never required because it always has a default
        self.arg['required'] = False

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


class PathArgGen(ArgumentGen):
    """
    - cli default must ensure cross-platform,
    - build variables $VAR$ are thus used and must not be expanded to their literal there
    """
    def __init__(self, name, arg):
        super().__init__(name, arg)
        self.default = self.arg['default'] if self.arg['default'] is not None else repr('')

    def generate(self):
        """output code lines"""
        return util.indent(f"""\
parser.add_argument(
    {self.shortSwitch}
    '{self.longSwitch}',
    action='{self.action}',
    dest='{self.dest}',
    type={self.arg['type']},
    default={repr(self.default)},
    required={self.arg['default'] is None},
    help='{self.arg['help']}'
)""")


#
# gui
#
class EntryGen:
    """
    - app.json input/output keys (names) can use snake_case, cameCase, PascalCase, or title/phrase case
    - code-gen will output standard casing instead: camelCase for args, title-case for entry captions
    """
    def __init__(self, name, arg):
        self.name = name
        self.arg = arg
        self.master = f'pg_{arg["group"].lower()}'
        self.title = self.arg.get('title') or util.convert_compound_cases(self.name, style='title')

    @staticmethod
    def create_codegen(name, arg):
        if 'choices' in arg:
            return OptionEntryGen(name, arg)
        dtype_codegen_map = {
            'bool': BoolEntryGen,
            'int': IntEntryGen,
            'float': FloatEntryGen,
            'str': TextEntryGen,
            'list': TextEntryGen,
            'file': FileEntryGen,
            'folder': FolderEntryGen,
        }
        return dtype_codegen_map[arg['type']](name, arg)

    def generate(self):
        raise NotImplementedError('subclass this!')

    def _get_name_repr(self):
        return repr(self.name)

    def _get_title_repr(self):
        return repr(self.title)

    def _get_help_repr(self):
        return repr(self.arg['help'])


class BoolEntryGen(EntryGen):
    def __init__(self, name, arg):
        super().__init__(name, arg)

    def generate(self):
        return [f"{self.name.lower()} = ui.BoolEntry({self.master}, {self._get_name_repr()}, {self._get_title_repr()}, {self.arg['default']}, {self._get_help_repr()}, {self.arg['presetable']})"]


class IntEntryGen(EntryGen):
    def __init__(self, name, arg):
        super().__init__(name, arg)
        # must generate liberal code float('inf') when inf is involved
        rg_min = "float('-inf')" if self.arg['range'][0] is None else int(self.arg['range'][0])
        rg_max = "float('inf')" if self.arg['range'][1] is None else int(self.arg['range'][1])
        self.range = f'[{rg_min}, {rg_max}]'
        self.step = self.arg.get('step') or 1

    def generate(self):
        return [f"{self.name.lower()} = ui.IntEntry({self.master}, {self._get_name_repr()}, {self._get_title_repr()}, {self.arg['default']}, {self._get_help_repr()}, {self.arg['presetable']}, {self.range}, {self.step})"]


class FloatEntryGen(EntryGen):
    def __init__(self, name, arg):
        super().__init__(name, arg)
        rg_min = "float('-inf')" if self.arg['range'][0] is None else float(self.arg['range'][0])
        rg_max = "float('inf')" if self.arg['range'][1] is None else float(self.arg['range'][1])
        self.range = f'[{rg_min}, {rg_max}]'
        self.step = self.arg.get('step') or 0.1
        self.precision = self.arg.get('precision') or 2

    def generate(self):
        return [f"{self.name.lower()} = ui.FloatEntry({self.master}, {self._get_name_repr()}, {self._get_title_repr()}, {self.arg['default']}, {self._get_help_repr()}, {self.arg['presetable']}, {self.range}, {self.step}, {self.precision})"]


class TextEntryGen(EntryGen):
    def __init__(self, name, arg):
        super().__init__(name, arg)

    def generate(self):
        return [f"{self.name.lower()} = ui.TextEntry({self.master}, {self._get_name_repr()}, {self._get_title_repr()}, {repr(self.arg['default'])}, {self._get_help_repr()}, {self.arg['presetable']}, )"]


class FileEntryGen(EntryGen):
    """
    - accept empty path for app-core to fill in
    """
    def __init__(self, name, arg):
        super().__init__(name, arg)
        # CAUTION
        # - if path is required, default will be null,
        # - but text widget will need it to be text, so we set it to empty string
        # - e.g., $APPDATA$/$APP$ => osp.join(util.get_platform_appdata_dir(), self.appConfig['name'])
        self.default = self._resolve_appconfig_path(self.arg['default'], repr(''))
        self.startDir = self._resolve_appconfig_path(self.arg['startDir'],  _build_var_map['$HOME$'])

    def generate(self):
        """
        - default uses osp.join() and should be used as code literal
        """
        return [f"{self.name.lower()} = ui.FileEntry({self.master}, {self._get_name_repr()}, {self._get_title_repr()}, {self.default}, {self._get_help_repr()}, {self.arg['presetable']}, {repr(self.arg['range'])}, {self.startDir})"]

    @staticmethod
    def _resolve_appconfig_path(path, fallback):
        """
        - assume all app-config paths use forward-slashes / as path separator
        """
        if path is None:
            return fallback
        path_comps = [osp.normpath(util.substitute_keywords(comp, _build_var_map, useliteral=True)) for comp in path.split('/')]
        for p, pc in enumerate(path_comps):
            if not pc.startswith('util.'):
                path_comps[p] = repr(pc)
        path_arg_list = ', '.join(path_comps)
        return f'osp.join({path_arg_list})'


class FolderEntryGen(EntryGen):
    def __init__(self, name, arg):
        super().__init__(name, arg)
        self.default = self._resolve_appconfig_path(self.arg['default'], repr(''))
        self.startDir = self._resolve_appconfig_path(self.arg['startDir'],  _build_var_map['$HOME$'])

    def generate(self):
        return [f"{self.name.lower()} = ui.FolderEntry({self.master}, {self._get_name_repr()}, {self._get_title_repr()}, {repr(self.default)}, {self._get_help_repr()}, {self.arg['presetable']}, {repr(self.startDir)})"]

    @staticmethod
    def _resolve_appconfig_path(path, fallback):
        """
        - assume all app-config paths use forward-slashes / as path separator
        """
        if path is None:
            return fallback
        path_comps = [osp.normpath(util.substitute_keywords(comp, _build_var_map, useliteral=True)) for comp in path.split('/')]
        for p, pc in enumerate(path_comps):
            if not pc.startswith('util.'):
                path_comps[p] = repr(pc)
        path_arg_list = ', '.join(path_comps)
        return f'osp.join({path_arg_list})'


class OptionEntryGen(EntryGen):
    def __init__(self, name, arg):
        super().__init__(name, arg)
        self.isMultiOpts = self.arg['range'][1] is None or self.arg['range'][1] > 1

    def generate(self):
        cls = 'MultiOptionEntry' if self.isMultiOpts else 'SingleOptionEntry'
        return [f"{self.name.lower()} = ui.{cls}({self.master}, {self._get_name_repr()}, {self._get_title_repr()}, {repr(self.arg['choices'])}, {repr(self.arg['default'])}, {self._get_help_repr()}, {self.arg['presetable']})"]


#
# output
#
class OutputEntryGen(EntryGen):
    """
    - TODO: support read-only list
    """
    def __init__(self, name, arg):
        arg['group'] = 'output'
        super().__init__(name, arg)

    @staticmethod
    def create_codegen(name, arg):
        dtype_codegen_map = {
            'bool': OutputEntryGen,
            'int': OutputEntryGen,
            'float': OutputEntryGen,
            'str': OutputEntryGen,
            'file': OutputPathEntryGen,
            'folder': OutputPathEntryGen,
        }
        return dtype_codegen_map[arg['type']](name, arg)

    def generate(self):
        return [f"out_{self.name.lower()} = ui.ReadOnlyEntry({self.master}, {self._get_name_repr()}, {self._get_title_repr()}, {repr(self.arg['default'])}, {self._get_help_repr()})"]


class OutputPathEntryGen(OutputEntryGen):
    def __init__(self, name, arg):
        super().__init__(name, arg)

    def generate(self):
        return [f"out_{self.name.lower()} = ui.ReadOnlyPathEntry({self.master}, {self._get_name_repr()}, {self._get_title_repr()}, {repr(self.arg['default'])}, {self._get_help_repr()})"]


#
# controller
#
class ControllerGen:
    """
    - generate and update controller code
    - protect custom code on updates
    - user must select only the applicable code and merge by hand
    - a diff-tool is recommended
    - TODO: auto-merge
    """

    def __init__(self, appcfg, srcfile):
        self.appConfig = appcfg
        self.srcFile = srcfile
        template_basecls_map = {
            'form': 'ui.FormController',
            'onoff': 'ui.FormController',
            # more factory controllers to come ...
            # custom controller is recommended to derive from FormController
            'custom': 'CustomController',
        }
        self.baseClass = template_basecls_map[self.appConfig['template']]

    @staticmethod
    def create_codegen(appcfg, srcfile):
        """
        - both form and realtime apps share form controller where realtime app's app-config will set up tracers
        """
        template_cls_map = {
            'form': 'FormControllerGen',
            'onoff': 'FormControllerGen',
            'custom': 'ControllerGen',
        }
        return globals()[f'{template_cls_map[appcfg["template"]]}'](appcfg, srcfile)

    def generate(self):
        return ['# CUSTOM CONTROLLER: IMPLEMENT IT IN control.py']

    @staticmethod
    def _create_event_handler(name, arg):
        """
        - any callback registered on argument
        """
        return ''


class FormControllerGen(ControllerGen):
    def __init__(self, appcfg, srcfile):
        super().__init__(appcfg, srcfile)
        reflect_out_code_lines = [f'self.model[{repr(out_argname)}] = out.{out_argname}' for out_argname in self.appConfig['output'].keys()]
        if reflect_out_code_lines:
            reflect_out_code_lines += ['self.update_view()']
        self.reflectOutCode = util.indent('\n'.join(reflect_out_code_lines), 8)

    def generate(self):
        util.substitute_keywords_in_file(self.srcFile, {
            '{{BASE_CONTROLLER}}': self.baseClass,
            '{{REFLECT_OUTPUT}}': self.reflectOutCode,
        }, useliteral=True)
        # load skeleton
        code_lines = util.load_lines(self.srcFile, rmlineend=True)
        # lazy-add event handlers to traceable args
        traceable_args = {name: arg for name, arg in self.appConfig['input'].items() if arg.get('trace')}
        code_lines += [line for name, arg in traceable_args.items() for line in self._create_event_handler(name, arg)]
        return code_lines

    @staticmethod
    def _create_event_handler(name, arg):
        """
        - add value tracer to argument
        """
        return f"""\
    def on_{name.lower()}_changed(self, name, var, index, mode):
        pass

""".splitlines()
