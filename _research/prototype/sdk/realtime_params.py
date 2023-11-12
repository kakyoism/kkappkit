#!/usr/bin/env python

"""
Test app of kkGUI's realtime mode. Control a sine tone.

Dependencies: pip install python-osc

Features
- CLI and GUI modes depending on whether user gives command options;
- Vertical parameter rack using factory methods parsing JSON configs;
"""

# Import built-in modules.
import sys
from os.path import abspath, basename, dirname, splitext
from queue import Queue
import subprocess
import threading

# Import 3rd-party modules.
# from pythonosc import osc_message_builder
from pythonosc import udp_client


# Metadata
__author__ = "Beinan Li"
__copyright__ = "Copyright $year$, Beinan Li"
__credits__ = ["Beinan Li"]
__license__ = "MIT"
__maintainer__ = "Beinan Li"
__email__ = "li.beinan@gmail.com"
__version__ = "0.1.2"


_basename = splitext(basename(__file__))[0]
_script_dir = abspath(dirname(__file__))

sys.path.append(dirname(_script_dir))
# Import project modules.
import kkgui as ui
import util


_progress_queue = Queue()


class RtpcMan:
    def __init__(self, ip, port):
        self.sender = udp_client.SimpleUDPClient(ip, port)
        self.guiHandlers = {
            'oscillator': {'OnChange': self.on_osc},
            'frequency': {'OnChange': self.on_freq},
            'gain': {'OnChange': self.on_gain},
        }

    def on_osc(self, var, name, elem, mode):
        print(f'{name=}, {elem=}, {mode=}, value={var.get_data()}')
        # oscillators = ["Sine",
        #                "Triangular",
        #                "Square",
        #                "Sawtooth",
        #                "White Noise",
        #                "Pink Noise"]
        self.sender.send_message(f'/{name}', var.get_data())

    def on_freq(self, var, name, elem, mode):
        print(f'{name=}, {elem=}, {mode=}, value={var.get_data()}')
        self.sender.send_message(f'/{name}', var.get_data())

    def on_gain(self, var, name, elem, mode):
        print(f'{name=}, {elem=}, {mode=}, value={var.get_data()}')
        self.sender.send_message(f'/{name}', var.get_data())

    def stop(self):
        """
        CAUTION:
        Do not use a single state to control both play and stop.
        Otherwise, scheduler will keep shooting events when it's on and explode.
        """
        self.sender.send_message('/stop', 1)
        _progress_queue.put(('/stop', 100))

    def play(self):
        self.sender.send_message('/play', 1)
        _progress_queue.put(('/start', 0))

    def quit(self):
        self.sender.send_message('/stop', 1)
        self.sender.send_message('/quit', 1)


_RTPC = RtpcMan('127.0.0.1', 10000)


def threaded_main():
    """
    Run non-blocking task.
    Use daemon because we must finish writing image even after UI quits.
    :return:
    """
    thread = threading.Thread(target=main,
                              args=([sys.argv[0], '-c'],),
                              daemon=True)
    thread.start()


def main(argv):
    app_info = {
        'Script': __file__,
        'Task': 'Run a tone generator and support RTPC.',
        'Version': __version__
    }
    args = util.parse_args_config(argv, app_info)
    config = util.load_json(args.cfg_file)
    logger = util.build_logger(__file__)

    # Run external process
    try:
        cmd = [config['engine']['Value'], config['script']['Value'], '-odac']
        logger.info(' '.join(cmd))
        completed = subprocess.run(cmd,
                                   check=True,
                                   shell=False,
                                   stdout=subprocess.PIPE)
    except subprocess.CalledProcessError as err:
        logger.error(err)
    else:
        logger.info('returncode: {}'.format(completed.returncode))
        logger.info('Have {} bytes in stdout: {!r}'.format(
            len(completed.stdout), completed.stdout.decode('utf-8'))
        )


def run_gui():
    """Run under GUI and non-verbose mode."""
    # sys.settrace(util.trace_calls_and_returns)
    root = ui.build_script_launcher(
        title=_basename,
        app_dir=_script_dir,
        progress_queue=_progress_queue,
        handlers={
            'OnQuit': _RTPC.quit,
            'OnSubmit': _RTPC.play,
            'OnCancel': _RTPC.stop,
            'Watchers': {
                'oscillator': {'OnChange': _RTPC.on_osc},
                'frequency': {'OnChange': _RTPC.on_freq},
                'gain': {'OnChange': _RTPC.on_gain},
            }
        },
        window_size=(768, 300),
        progress_mode='indeterminate'
    )
    threaded_main()  # Launch Csound and keep it running.
    root.mainloop()


if __name__ == '__main__':
    if util.is_gui_mode(sys.argv):
        run_gui()
    else:
        sys.exit(main(sys.argv))
