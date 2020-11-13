#!/usr/bin/env python

"""
Utility lib for personal projects, supports py3 only.

Covering areas:
    - Logging;
    - Config save/load;
    - Decoupled parameter server-client arch;
"""

# Import std-modules.
import argparse
import collections
import cProfile as profile
import functools
import hashlib
import json
import logging
import logging.config
import math
import multiprocessing
import os
from os.path import abspath, basename, dirname, exists, isfile, isdir, join, split, splitext
from pprint import pprint, pformat
import pstats
import subprocess
import sys
import tempfile
import threading
import traceback

# Metadata
__author__ = "Beinan Li"
__copyright__ = "Copyright $year$, Beinan Li"
__credits__ = ["Beinan Li"]
__license__ = "MIT"
__maintainer__ = "Beinan Li"
__email__ = "li.beinan@gmail.com"
__version__ = "0.6.0"


#
# Globals
#
_script_dir = abspath(dirname(__file__))
TXT_CODEC = 'utf-8'  # Importable.
MAIN_CFG_FILENAME = 'app.json'
DEFAULT_CFG_FILENAME = 'default.json'


class LowPassLogFilter(object):
    """
    Logging filter: Show log messages below input level.
    - CRITICAL = 50
    - FATAL = CRITICAL
    - ERROR = 40
    - WARNING = 30
    - WARN = WARNING
    - INFO = 20
    - DEBUG = 10
    - NOTSET = 0
    """
    def __init__(self, level):
        self.__level = level

    def filter(self, log):
        return log.levelno <= self.__level


class HighPassLogFilter(object):
    """Logging filter: Show log messages above input level."""
    def __init__(self, level):
        self.__level = level

    def filter(self, log):
        return log.levelno >= self.__level


class BandPassLogFilter(object):
    def __init__(self, levelbounds):
        self.__levelbounds = levelbounds

    def filter(self, log):
        return self.__levelbounds[0] <= log.levelno <= self.__levelbounds[1]


def build_default_logger(logdir, name=None, cfgfile=None, verbose=False):
    """
    Create per-file logger and output to shared log file.
    - If found config file under script folder, use it;
    - Otherwise use default config: save to /project_root/project_name.log.
    - 'filename' in config is a filename; must prepend folder path to it.
    :logdir: directory the log file is saved into.
    :name: basename of the log file,
    :cfgfile: config file in the format of dictConfig.
    :return: logger object.
    """
    try:
        os.makedirs(logdir)
    except:
        pass

    cfg_file = cfgfile or join(_script_dir, 'logging.json')
    logging_config = None
    try:
        if sys.version_info.major > 2:
            with open(cfg_file, 'r', encoding=TXT_CODEC, errors='backslashreplace', newline=None) as f:
                text = f.read()
        else:
            with open(cfg_file, 'rU') as f:
                text = f.read()
        # Add object_pairs_hook=collections.OrderedDict hook for py3.5 and lower.
        logging_config = json.loads(text, object_pairs_hook=collections.OrderedDict)
        logging_config['handlers']['file']['filename'] = join(logdir, logging_config['handlers']['file']['filename'])
    except Exception:
        filename = name or basename(basename(logdir.strip('\\/')))
        log_path = join(logdir, '{}.log'.format(filename))
        logging_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "info_lpf": {
                  "()": "util.LowPassLogFilter",
                  "level": 10 if verbose else 20,
                },
                "info_bpf": {
                  "()": "util.BandPassLogFilter",
                  "levelbounds": [10, 20] if verbose else [20, 20],
                },
                "warn_hpf": {
                  "()": "util.HighPassLogFilter",
                  "level": 30
                }
            },
            "formatters": {
                "console": {
                    "format": "%(asctime)s: %(levelname)s: %(module)s: %(lineno)d: \n%(message)s\n"
                },
                "file": {
                    "format": "%(asctime)s: %(levelname)s: %(pathname)s: %(lineno)d: \n%(message)s\n"
                }
            },
            "handlers": {
                    "console": {
                        "level": "DEBUG" if verbose else "INFO",
                        "formatter": "console",
                        "class": "logging.StreamHandler",
                        "stream": "ext://sys.stdout",
                        "filters": ["info_bpf"]
                    },
                    "console_err": {
                        "level": "WARN",
                        "formatter": "console",
                        "class": "logging.StreamHandler",
                        "stream": "ext://sys.stderr",
                        "filters": ["warn_hpf"]
                    },
                    "file": {
                        "level": "DEBUG",
                        "formatter": "file",
                        "class": "logging.FileHandler",
                        "encoding": "utf-8",
                        "filename": log_path
                    }
            },
            "loggers": {
                "": {
                    "handlers": ["console", "console_err", "file"],
                    "level": "INFO",
                    "propagate": True
                },
                "default": {
                    "handlers": ["console", "console_err", "file"],
                    "level": "DEBUG",
                    "propagate": False
                }
            }
        }
    if name:
        logging_config['loggers'][name] = logging_config['loggers']['default']
    logging.config.dictConfig(logging_config)
    return logging.getLogger(name or 'default')


_logger = build_default_logger(logdir=join(_script_dir, os.pardir, 'temp'))


def catch_unknown_exception(exc_type, exc_value, exc_traceback):
    """Global exception to handle uncaught exceptions"""
    exc_info = exc_type, exc_value, exc_traceback
    _logger.error('Unhandled exception: ', exc_info=exc_info)
    # _logger.exception('Unhandled exception: ')  # Only works in try-except block.
    # sys.__excepthook__(*exc_info)  # Keep this commented out to avoid message duplication.


sys.excepthook = catch_unknown_exception


def build_logger(srcpath, logpath=None):
    """
    Build per-file logger.
    :param srcpath: Path to source file.
    :param logpath: Path to log file, default to /same/dir/basename.log.
    :return: Logger object.
    """
    src_basename = basename(srcpath)

    # Must have to see DEBUG/INFO at all
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(src_basename)
    logger.setLevel(logging.DEBUG)

    # Hide dependency module's logging
    logger.propagate = False

    # Avoid redundant logs from duplicated handlers created by other modules.
    if len(logger.handlers) > 1:
        return logger

    # Console log for end-users: no debug messages.
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter(
        '%(levelname)s: %(name)s: %(message)s')
    )
    logger.addHandler(handler)

    if logpath is None:
        logpath = join(abspath(dirname(srcpath)), 'app.log')

    # Log file for coders: with debug messages.
    logdir = abspath(dirname(logpath))
    if not exists(logdir):
        os.makedirs(logdir)
    handler = logging.FileHandler(logpath)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter(
        '%(levelname)s: %(pathname)s: %(lineno)d: %(asctime)s: \n%(message)s\n')
    )
    logger.addHandler(handler)

    return logger


def format_error_message(situation, expected, got, suggestions, action):
    return '{}.\n\tExpected: {};\n\tGot: {};\n\tSuggestions: {};\n\tAction: {}.'.format(situation, expected, got, suggestions, action)


def is_cli_mode(argv):
    """Use CLI mode if found command line options."""
    return len(argv) > 1


def is_gui_mode(argv):
    """Use GUI mode if no command line options are found."""
    return len(argv) == 1  # no command line options, so run GUI.


def is_multiline(text):
    return len(text.strip().split('\n')) > 1


def is_python3():
    return sys.version_info[0] > 2


def load_json(path):
    """
    Load Json configuration file.
    :param path: path to the config file
    :return: config as a dict
    """
    if is_python3():
        with open(path, 'r', encoding=TXT_CODEC, errors='backslashreplace', newline=None) as f:
            text = f.read()
    else:
        with open(path, 'rU') as f:
            text = f.read()
    # Add object_pairs_hook=collections.OrderedDict hook for py3.5 and lower.
    return json.loads(text, object_pairs_hook=collections.OrderedDict)


def save_json(path, config):
    """
    Use io.open(), aka open() with py3 to produce a file object that encodes
    Unicode as you write, then use json.dump() to write to that file.
    Validate keys to avoid JSON and program out-of-sync.
    """
    if is_python3():
        with open(path, 'w', encoding=TXT_CODEC) as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    else:
        with open(path, 'w') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)


def parse_args_config(argv, app_info):
    """
    Argrument parser for config-based controls.
    :param argv: sys.argv;
    :param app_info: {'Script': /path/to/script, 'Task': for what,
    'Version': __version__};
    :return: argument parsed.
    """
    name = 'python {}'.format(app_info['Script'])
    script_dir = abspath(dirname(app_info['Script']))
    cfg_file = abspath(join(script_dir, MAIN_CFG_FILENAME))
    default_cfg_file = join(script_dir, DEFAULT_CFG_FILENAME)
    desc = """
{}

Parameters are defined in config files in app folder.
App folder has exactly one pair of config files.
    - app.json: used with -c option under CLI mode, and under GUI mode.
          Control values are saved here on launch.
    - default.json: used as fallback config and for resetting GUI.
                    It should be updated sparingly by user.
    """.format(app_info['Task'])

    epilog = """
examples:

# Run under command line (CLI) mode using main config file
python -c {}

# Run under CLI mode using specified config file
python -C /path/to/myconfig.json {}

# Run under GUI mode
python {} 
or use shell integration, e.g., Explorer or Finder.
        """.format(app_info['Script'], app_info['Script'], app_info['Script'])
    parser = argparse.ArgumentParser(
        prog=name,
        description=desc,
        add_help=True,
        epilog=epilog,
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(
        '-v',
        '--version',
        action='version',
        version='%(prog)s {}'.format(app_info['Version'])
    )
    parser.add_argument(
        '-c',
        '--commandline',
        action='store_true',
        default=False,
        help='Run in command line mode (CLI) with main config if set.'
    )
    parser.add_argument(
        '-C',
        '--config',
        # nargs=1,   # CAUTION: Ignore narg, otherwise you get a list.
        action='store',
        dest='cfg_file',
        default=cfg_file,
        help='Path to config file, default to {} .'.format(default_cfg_file))
    # CLI logging is quiet; log file is verbose.
    parser.add_argument(
        '-V',
        '--verbose',
        action='store_true',
        dest='verbose',
        default=False,
        help='Use verbose logging if true, otherwise quiet, default to False.'
    )

    # CAUTION:
    # Must ignore argv[0], i.e., script name,
    # to avoid "error: unrecognized arguments: test.py"
    return parser.parse_args(argv[1:])


def query_yes_no(question, default=True):
    """Ask a yes/no question via standard input and return the answer.

    If invalid input is given, the user will be asked until
    they acutally give valid input.

    Args:
        question(str):
            A question that is presented to the user.
        default(bool|None):
            The default value when enter is pressed with no value.
            When None, there is no default value and the query
            will loop.
    Returns:
        A bool indicating whether user has entered yes or no.

    Side Effects:
        Blocks program execution until valid input(y/n) is given.
    """
    input_ = input if sys.version_info.major > 2 else raw_input
    yes_list = ['yes', 'y']
    no_list = ['no', 'n']

    default_dict = {  # default => prompt default string
        None: '[y/n]',
        True: '[Y/n]',
        False: '[y/N]',
    }

    default_str = default_dict[default]
    prompt_str = '{}\n{}'.format(question, default_str) \
        if question else '{}'.format(default_str)

    while True:
        choice = input_(prompt_str).lower()

        if not choice and default is not None:
            return default
        if choice in yes_list:
            return True
        if choice in no_list:
            return False

        notification_str = "Please type in 'y' or 'n'"
        print(notification_str)


def trace_calls_and_returns(frame, event, arg):
    co = frame.f_code
    func_name = co.co_name
    if func_name == 'write':
        # Ignore write() calls from printing
        return
    line_no = frame.f_lineno
    filename = co.co_filename
    if event == 'call':
        print('* Call to {} on line {} of {}'.format(
            func_name, line_no, filename))
        return trace_calls_and_returns
    elif event == 'return':
        print('* {} => {}'.format(func_name, arg))
    return


def threaded_main(target, daemon=True):
    """
    Run main task without blocking GUI for realtime apps.
    Assume:
    - parameters are from config file.
    - no thread communication.
    :param target: main function.
    :param daemon: True if backend must finish work after GUI quits.
    :return:
    """
    thread = threading.Thread(target=target,
                              args=([sys.argv[0], '-c'],),
                              daemon=daemon)
    thread.start()


def get_md5_checksum(file):
    """Compute md5 checksum of a file."""
    if not isfile(file):
        return None
    myhash = hashlib.md5()
    with open(file, 'rb') as f:
        while True:
            b = f.read(8096)
            if not b:
                break
            myhash.update(b)
    return myhash.hexdigest()


def logprogress(msg='Task', loghook=_logger.info, errorhook=_logger.error):
    def wrap(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            loghook("Progress: Start {} ...".format(msg))
            try:
                response = function(*args, **kwargs)
            except Exception as error:
                errorhook("Function '{}' raised {} with error '{}'.".format(function.__name__, error.__class__.__name__, str(error)))
                raise error
            loghook("Progress: Done.")
            return response
        return wrapper
    return wrap


def logcall(msg='trace', loghook=_logger.debug, errorhook=_logger.error):
    def wrap(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            loghook("Calling function '{}' with args={} kwargs={}: {}.".format(function.__name__, args, kwargs, msg))
            try:
                response = function(*args, **kwargs)
            except Exception as error:
                loghook("Function '{}' raised {} with error '{}'.".format(function.__name__, error.__class__.__name__, str(error)))
                raise error
            loghook("Function '{}' returned {}.".format(function.__name__, response))
            return response
        return wrapper
    return wrap


def organize_concurrency(ntasks, nprocs=None, useio=False):
    """
    Suggest concurrency approach based on tasks and number of processes.
    - Use Processes when processes are few or having I/O tasks.
    - Use Pool for many processes or no I/O.
    - Use sequential when tasks are
    :param ntasks: number of total tasks.
    :param nprocs: number of processes, None means to let algorithm decide.
    :param useio: are we I/O-bound?
    :return: dict of all needed parameters.
    """
    if ntasks <= 1:
        return {'Type': 'Sequential'}

    # manual process allocation
    if not nprocs:
        nprocs = multiprocessing.cpu_count()

    # io-bound
    if useio:
        nprocs = 10
        return {
            'Type': 'Thread',
            'Count': nprocs
        }

    # cpu-bound
    # # brute-force schedule
    # tasks_per_proc = int(math.floor(float(ntasks) / float(nprocs)))
    # ranges = [(i * tasks_per_proc, (i + 1) * tasks_per_proc if i < nprocs - 1 else ntasks) for i in range(nprocs)]
    return {
        'Type': 'Process',
        'Count': nprocs
    }


def ranged_worker(worker, rg, shared, lock):
    results = [worker(shared['Tasks'][t]) for t in range(rg[0], rg[1])]
    # pprint(results)
    with lock:
        tmp = shared['Results']
        for r, result in enumerate(results):
            tmp.append(result)
        shared['Results'] = tmp
    # pprint('tmp: {}'.format(tmp))


def execute_concurrency(worker, shared, lock, algorithm):
    """
    Execute tasks and return results, based on algorithm.
    - worker is unit sequential worker, using single arg.
    - worker returns result as (task['Index'], value).
    - shared is a manager().dict().
    - shared has keys: Title, Tasks.
    - shared['Tasks']: tuple of args for each task worker instance
    - shared['Tasks'][i] has keys: Title, Index, Args, Result
        - Title: info for progress report
        - Index: order of tasks, None for unordered
        - Args: worker input args
        - Result: worker returned results in order
    """
    global _logger
    # TODO: measure timeout for .join()
    if algorithm['Type'] == 'Sequential':
        results = []
        for t, task in enumerate(shared['Tasks']):
            _logger.debug('Execute {} in order: {} of {}: {}'.format(shared['Title'], t+1, len(shared['Tasks']), task['Title']))
            results.append(worker(task))
        return [result[1] for result in results]
    elif algorithm['Type'] == 'Process':
        _logger.debug('Execute {} in pool of {} processes ...'.format(shared['Title'], algorithm['Count']))
        #
        # Known Issue:
        # - https://bugs.python.org/issue9400
        # - Python multiprocessing.Pool is buggy at join()
        # Reference:
        # - https://stackoverflow.com/questions/15314189/python-multiprocessing-pool-hangs-at-join
        #
        results = []
        try:
            with multiprocessing.Pool(processes=algorithm['Count']) as pool:
                results = pool.map(worker, shared['Tasks'])
                pool.close()
                pool.join()
        except Exception:
            traceback.print_exc()
        # Results are always sorted in pool.
        return [result[1] for result in results]
    elif algorithm['Type'] == 'Thread':
        import concurrent.futures
        _logger.debug('Execute {} in pool of {} threads ...'.format(shared['Title'], algorithm['Count']))
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=algorithm['Count'])
        results = executor.map(worker, shared['Tasks'])
        return [result[1] for result in results]
    raise ValueError(format_error_message('Found undefined concurrency algorithm.', expected='One of: {}, {}, {}'.format('Sequential', 'Pool', 'Process'), got=algorithm['Type'], suggestions=('Check if this API is up to date', 'retry me'), action='Aborted'))


def profile_runs(funcname, modulefile, nruns=5):
    module_name = splitext(basename(modulefile))[0]
    stats_dir = join(abspath(dirname(modulefile)), 'stats')
    try:
        os.makedirs(stats_dir)
    except Exception:
        traceback.print_exc()
    for i in range(nruns):
        stats_file = join(stats_dir, 'profile_{}_{}.pstats.log'.format(funcname, i))
        profile.runctx('import {}; print({}, {}.{}())'.format(module_name, i, module_name, funcname), globals(), locals(), stats_file)
    # Read all 5 stats files into a single object
    stats = pstats.Stats(join(stats_dir, 'profile_{}_0.pstats.log'.format(funcname)))
    for i in range(1, nruns):
        stats.add(join(stats_dir, 'profile_{}_{}.pstats.log'.format(funcname, i)))
    # Clean up filenames for the report
    stats.strip_dirs()
    # Sort the statistics by the cumulative time spent
    # in the function
    stats.sort_stats('cumulative')
    stats.print_stats()


class RerunLock:
    """Lock process from reentering when seeing lock file on disk."""
    def __init__(self, name, folder=None, infohook=_logger.info, warnhook=_logger.warning, errorhook=_logger.error):
        filename = 'lock_{}'.format(name) if name else 'lock_{}'.format(next(tempfile._get_candidate_names()))
        self.lockFile = join(folder, filename) if folder else join(_script_dir, os.pardir, filename)
        self.infoHook = infohook
        self.warnHook = warnhook
        self.errorHook = errorhook

    def lock(self):
        if not self.is_locked():
            with open(self.lockFile, 'w') as f:
                pass
            return True
        else:
            self.warnHook('Rerun disabled using file: {}. Unlock it before locking again. Aborted. You can ignore this message if your program is already running as planned.'.format(self.lockFile))
            return False

    def unlock(self):
        try:
            os.remove(self.lockFile)
            self.infoHook('Rerun enabled after removing lock file: {}. You can ignore this message if your program finishes with success.'.format(self.lockFile))
        except FileNotFoundError:
            self.warnHook('Failed to find lock file: {}. Rerun is enabled. Ignored.'.format(self.lockFile))
        except Exception:
            failure = traceback.format_exc()
            self.errorHook('{}\nFailed to enable rerun by deleting reentrance lock file: {}. You must delete it by hand to rerun your program. Ignored.'.format(failure, self.lockFile))

    def is_locked(self):
        return exists(self.lockFile)


def rerun_lock(name, folder=None, infohook=_logger.info, warnhook=_logger.warning, errorhook=_logger.error):
    """Decorator for reentrance locking on functions"""
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            my_lock = None
            try:
                my_lock = RerunLock(name, folder, infohook, warnhook, errorhook)
                if not my_lock.lock():
                    return 1
                ret = f(*args, **kwargs)
            finally:  # Leave exception to global handler.
                my_lock.unlock()
            return ret
        return wrapper
    return decorator


class SingletonDecorator:
    """
    Decorator to build Singleton class, single-inheritance only.
    Usage:
        class MyClass: ...
        myobj = SingletonDecorator(MyClass, args, kwargs)
    """
    def __init__(self, klass):
        self.klass = klass
        self.instance = None

    def __call__(self, *args, **kwargs):
        if self.instance is None:
            self.instance = self.klass(*args, **kwargs)
        return self.instance


class _Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(_Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Singleton(_Singleton('SingletonMeta', (object,), {})):
    pass


def test():
    pass


if __name__ == '__main__':
    test()
