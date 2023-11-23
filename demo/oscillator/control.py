import time

# 3rd party
import kkpyutil as util
import pythonosc.udp_client as osc_client
# project
import kkpyui as ui
import imp


class ControllerImp:
    """
    - implement all gui event-handlers
    """
    def __init__(self, ctrlr, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.controller = ctrlr
        self.sender = osc_client.SimpleUDPClient('127.0.0.1', 10000)
        self.playing = False

    def submit(self, event=None):
        """
        - assume csound has started
        """
        if self.playing:
            return False
        self.controller.update()
        options = ['Sine', 'Square', 'Sawtooth']
        self.sender.send_message('/oscillator', options.index(self.controller.model['General']['Oscillator']))
        self.sender.send_message('/frequency', self.controller.model['General']['Frequency (Hz)'])
        self.sender.send_message('/gain', self.controller.model['General']['Gain (dB)'])
        self.sender.send_message('/play', 1)
        self.controller.set_progress('/start', 0, 'Playing ...')
        self.playing = True
        return True

    def cancel(self, event=None):
        self.sender.send_message('/play', 0)
        self.controller.set_progress('/stop', 100, 'Stopped')
        time.sleep(0.1)
        self.playing = False

    def init(self, event=None):
        self.controller.init()
        self.controller.update()
        cmd = ['csound', self.controller.model['General']['Csound Script'][0], '-odac']
        util.run_daemon(cmd)
        # time.sleep(0.8)

    def term(self, event=None):
        self.cancel()
        util.kill_process_by_name('csound')

    def on_freq_changed(self, name, var, index, mode):
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
