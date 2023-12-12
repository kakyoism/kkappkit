import os.path as osp
import time
# 3rd party
import kkpyutil as util
import pythonosc.udp_client as osc_client
# project
import kkpyui as ui
import impl


class Controller(ui.FormController):
    """
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sender = osc_client.SimpleUDPClient('127.0.0.1', 10000)
        self.playing = False
        self.curEngine = None

    def on_open_help(self):
        """
        - implement this to open help URL/file in default browser
        """
        pass

    def on_open_log(self):
        """
        - implement this to open log file in default browser
        """
        pass

    def on_report_issue(self):
        """
        - implement this to receive user feedback
        """
        pass

    def on_startup(self):
        scpt = self.model['engine']
        if not osp.isfile(scpt):
            if not util.confirm(f'Missing user Csound script: {scpt}', 'Proceed to use default script? Otherwise switch to a different script and restart app', title='Warning'):
                self.on_quit(None)
                return
            scpt = osp.abspath(f'{osp.dirname(__file__)}/../res/tonegen.csd')
            # refresh entry view
            self.model['engine'] = scpt
            self.update_view()
        # CAUTION
        # - because sandboxed app cannot access system PATH, must use absolute path to executable
        # - assume csound is installed by chocolatey and homebrew
        # - use their default installation paths
        exe = osp.normpath('c:/program files/csound/bin/csound.exe') if util.PLATFORM == 'Windows' else '/usr/local/bin/csound'
        cmd = [exe, scpt, '-odac']
        util.run_daemon(cmd)
        self.curEngine = self.model['engine']
        # time.sleep(0.8)

    def on_shutdown(self, event=None) -> bool:
        if not super().on_shutdown():
            return False
        self.on_cancel()
        util.kill_process_by_name('csound')
        return True

    def run_task(self):
        if self.playing:
            return False
        self.update_model()
        print(f'{self.curEngine=}; {self.model["engine"]=}')
        if self.curEngine != self.model['engine']:
            self.on_shutdown()
            self.on_startup()
        options = ['Sine', 'Square', 'Sawtooth']
        self.sender.send_message('/oscillator', options.index(self.model['oscillator']))
        self.sender.send_message('/frequency', self.model['frequency'])
        self.sender.send_message('/gain', self.model['gain'])
        self.sender.send_message('/play', 1)
        self.set_progress('/start', 0, 'Playing ...')
        self.playing = True
        return True

    def on_cancel(self, event=None):
        self.sender.send_message('/play', 0)
        self.set_progress('/stop', 100, 'Stopped')
        time.sleep(0.1)
        self.playing = False
        super().on_cancel(event)

    def on_frequency_changed(self, name, var, index, mode):
        print(f'{name=}={var.get()}, {index=}, {mode=}')
        self.sender.send_message('/frequency', var.get())

    def on_gain_changed(self, name, var, index, mode):
        print(f'{name=}={var.get()}, {index=}, {mode=}')
        self.sender.send_message('/gain', var.get())

    def on_oscillator_changed(self, name, var, index, mode):
        print(f'{name=}={var.get()}, {index=}, {mode=}')
        self.sender.send_message('/play', 0)
        time.sleep(0.1)
        self.sender.send_message('/oscillator', var.get())
        self.sender.send_message('/play', 1)
