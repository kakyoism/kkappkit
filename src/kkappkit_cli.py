import argparse

import kkappkit_core as core


def main():
    parser = create_parser()
    add_arguments(parser)
    worker = core.Core(parser.parse_args())
    worker.main()


def create_parser():
    return argparse.ArgumentParser(
        prog='kkappkit',
        description='Code-generator for building small tool applications with Python and Tkinter',
        add_help=True,
        epilog="""\
# =============
# EXAMPLES
# =============
# generate an empty app-config for a new app
kkappkit/run -n my_app

# after filling up app-config and its sub-configs, generate or update app according to the entire config set
kkappkit/run -g /path/to/my_app/app.json

# same as above, but backup and erase the existing content, then start anew"
kkappkit/run -g /path/to/my_app/my_app.kak.json -f

# =============
# REMARKS
# =============
Build Variables:
- ${name}: the name of the target app
- ${cli}: the path to the app's commandline interface script
""",
        formatter_class=argparse.RawTextHelpFormatter
    )


def add_arguments(parser):
    parser.add_argument(
        '-n',
        '--app-name',
        action='store',
        dest='appName',
        type=str,
        default='',
        required=True,
        help='the name of the target app'
    )
    parser.add_argument(
        '-p',
        '--parent-folder',
        action='store',
        dest='parDir',
        type=str,
        default='.',
        required=True,
        help='parent folder of the app'
    )
    parser.add_argument(
        '-f',
        '--force-overwrite',
        action='store_true',
        dest='forceOverwrite',
        default=False,
        required=False,
        help='force backup and overwrite the existing app project'
    )


if __name__ == '__main__':
    main()
