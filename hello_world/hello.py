# Import built-in modules.
import functools
import os
from os.path import abspath, basename, dirname, join, splitext
from queue import Queue
import sys

#
# Globals
#
__version__ = "0.0.1"
_basename = splitext(basename(__file__))[0]
_script_dir = abspath(dirname(__file__))
_progress_queue = Queue()

# Import project modules.
sys.path.append(join(_script_dir, os.pardir))
import kkgui as ui
import util


def main(argv):
    logger = util.build_logger(__file__)
    prompt = ui.Prompt(logger, is_gui=util.is_gui_mode(sys.argv))

    # Progress info and completion percentage.
    progress = (
        ('Initializing', 1),
        ('Working', 20),
        ('Done', 100)
    )

    # Make progress.
    stage = 0
    _progress_queue.put(progress[stage])

    # Help info to show under CLI mode.
    app_info = {
        'Script': __file__,
        'Task': 'Show a string and a number.',
        'Version': __version__
    }
    args = util.parse_args_config(argv, app_info)
    config = util.load_json(args.cfg_file)  # arg is a list under CLI.

    # Move the proressbar.
    stage += 1
    _progress_queue.put(progress[stage])

    # Do work.
    prompt.info('String: {}, Number: {}'.format(
        config['my_string']['Value'],
        config['my_number']['Value']))

    # Move the proressbar.
    stage += 1
    _progress_queue.put(progress[stage])
    return 0


def run_gui():
    """Run under GUI and non-verbose mode."""
    root = ui.build_script_launcher(
        title=_basename,
        app_dir=_script_dir,
        progress_queue=_progress_queue,
        handlers={
            'OnQuit': None,
            'OnSubmit': functools.partial(
                util.threaded_main,
                target=main),
            'OnCancel': None
        },
        window_size=(768, 300)
    )
    root.mainloop()


if __name__ == '__main__':
    if util.is_cli_mode(sys.argv):
        sys.exit(main(sys.argv))
    else:
        run_gui()
