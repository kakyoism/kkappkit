import os.path as osp
import time
# 3rd party
import kkpyutil as util
import pythonosc.udp_client as osc_client
# project
import kkpyui as ui
import impl


class ControllerImp:
    """
    - implement all gui event-handlers
    """
    def __init__(self, ctrlr, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.controller = ctrlr
        self.sender = osc_client.SimpleUDPClient('127.0.0.1', 10000)
        self.playing = False
        self.initialized = False

    def on_submit(self, event=None):
        """
        - assume csound has started
        """
        if self.playing:
            return False
        self.controller.update()
        options = ['Sine', 'Square', 'Sawtooth']
        self.sender.send_message('/oscillator', options.index(self.controller.model['General']['Waveform']))
        self.sender.send_message('/frequency', self.controller.model['General']['Frequency (Hz)'])
        self.sender.send_message('/gain', self.controller.model['General']['Gain (dB)'])
        self.sender.send_message('/play', 1)
        self.controller.set_progress('/start', 0, 'Playing ...')
        self.playing = True
        return True

    def on_cancel(self, event=None):
        self.sender.send_message('/play', 0)
        self.controller.set_progress('/stop', 100, 'Stopped')
        time.sleep(0.1)
        self.playing = False

    def on_activate(self, event=None):
        if self.initialized:
            return
        self.initialized = True
        self.controller.update()
        scpt = self.controller.model['General']['Csound Script'][0]
        if not osp.isfile(scpt):
            if not util.confirm(f'Missing user Csound script: {scpt}', 'Proceed to use default script? Otherwise switch to a different script and restart app', title='Warning'):
                self.on_term(None)
                return
            scpt = osp.join(osp.dirname(__file__), '../res/tonegen.csd')
            # refresh entry view
            self.controller.model['General']['Csound Script'][0] = scpt
            self.controller.reflect()
        # CAUTION
        # - because sandboxed app cannot access system PATH, must use absolute path to executable
        # - assume csound is installed by chocolatey and homebrew
        # - use their default installation paths
        exe = osp.normpath('c:/program files/csound/bin/csound.exe') if util.PLATFORM == 'Windows' else '/usr/local/bin/csound'
        cmd = [exe, scpt, '-odac']
        util.run_daemon(cmd)
        # time.sleep(0.8)

    def on_term(self, event=None):
        self.on_cancel()
        util.kill_process_by_name('csound')

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
