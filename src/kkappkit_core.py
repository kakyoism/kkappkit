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


class Result:
    def __init__(self, logger=None):
        self.succeeded: bool = False
        self.detail: str = ''
        self.advice: str = ''
        self.logger = logger

    def set_detail(self, title='', bullets=()):
        self.detail = self.create_brief(title, bullets)

    def set_advice(self, title='', bullets=()):
        self.advice = self.create_brief(title, bullets)

    def append_detail(self, title='', bullets=()):
        self.detail = f"""{self.detail}
{self.create_brief(title, bullets)}"""

    def append_advice(self, title='', bullets=()):
        self.advice = f"""{self.advice}
{self.create_brief(title, bullets)}"""

    def append_contact_advice(self, ids=()):
        if not ids:
            return
        id_list = [f'@{i}' for i in ids]
        self.advice = f"""{self.advice}. Contact: {', '.join(id_list)}."""

    @staticmethod
    def create_brief(title='', bullets=()):
        """
        create standard report paragraph, e.g.:
          title:
          - bullet 1
          - bullet 2
        """
        if not bullets:
            return title
        bullet_list = '\n'.join([f'- {p}' for p in bullets])
        return f"""{title}:
{bullet_list}""" if title else bullet_list

    def throw(self, errclass, detail=None, advice=None):
        assert issubclass(errclass, Exception)
        msg = json.dumps({
            'detail': detail or self.detail,
            'advice': advice or self.advice,
        }, ensure_ascii=False)
        err = errclass(msg)
        if self.logger:
            self.logger.exception(f'{err}')
        raise err

    def catch(self, exc: Exception):
        try:
            dmp = json.loads(str(exc))
        except json.JSONDecodeError as e:
            dmp = {
                'detail': f"""\
Unknown Exception in Service:

{str(exc)}""",
                'advice': 'Contact TechAudio Team for help',
            }
        self.succeeded = False
        self.detail = f"""\
{dmp['detail']}

<TRACEBACK>
Exception:
{traceback.format_exc()}
</TRACEBACK>"""
        self.advice = dmp['advice']


class Core:
    def __init__(self, args):
        self.args = args
        name = toml.load(osp.join(osp.dirname(__file__), 'pyproject.toml'))['tool']['poetry']['name']
        tmp_dir = osp.join(util.get_platform_tmp_dir(), name)
        session_dir = osp.join(tmp_dir, datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
        self.logger = util.build_default_logger(session_dir, name=name, verbose=True)
        self.res = Result(self.logger)
        self.root = osp.abspath(f'{osp.dirname(__file__)}/../')
        self.appPaths = types.SimpleNamespace(
            root=osp.join(self.args.parDir, self.args.appName),
        )
        self.appPaths.srcDir = osp.join(self.appPaths.root, 'src')
        self.appPaths.appCfg = osp.join(self.appPaths.srcDir, 'app.json')
        self.appPaths.depCfg = osp.join(self.appPaths.root, 'pyproject.toml')

    def main(self):
        self._validate_args()
        self._create_subdirs()
        if not self._init_app_proj():
            return
        self._init_source_files()
        self._generate_code()

    def _validate_args(self):
        pass

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

    def _init_app_proj(self):
        if not self.args.forceOverwrite and osp.exists(self.appPaths.depCfg):
            self.logger.info(f'project already exists: {self.appPaths.depCfg}; skipped init')
            return False
        util.run_cmd(['poetry', 'init', '-n'], cwd=self.appPaths.root)
        proj_config = toml.load('pyproject.toml')
        proj_config['tool']['poetry']['name'] = self.args.appName
        proj_config['tool']['poetry']['description'] = self.args.appName
        proj_config['tool']['poetry']['authors'] = [getpass.getuser()]
        return True

    def _init_source_files(self):
        src_files = (
            osp.abspath(f'{self.root}/src/template/default.app.json')
        )
        dst_files = (
            osp.abspath(f'{self.appPaths.root}/src/app.json')
        )
        for src, dst in zip(src_files, dst_files):
            if not self.args.forceOverwrite and osp.exists(dst):
                self.logger.info(f'{dst} already exists; skipped copying')
                continue
            util.copy_file(src, dst, isdstdir=True)

    def _generate_code(self):
        app_config = util.load_json(self.appPaths.appCfg)
        if is_new_app := not app_config['name']:
            self.res.throw(ValueError, 'app.json is empty; fill it up before retrying')
        # user has filled up app.json; generate code
        self._generate_cli()
        self._generate_gui()

    def _generate_cli(self):
        pass

    def _generate_gui(self):
        pass
