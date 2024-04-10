import argparse

import kkappkit_core as core


def main():
    parser = create_parser()
    add_arguments(parser)
    core.main(parser.parse_args())


def create_parser():
    return argparse.ArgumentParser(
        prog='kkappkit',
        description='Code-generator for building small desktop applications with Python and Tkinter',
        add_help=True,
        epilog="""\
# =============
# EXAMPLES
# =============
# generate an empty app-config for a new app
kkappkit/run -n my_app

# after filling up app-config and its sub-configs, generate or update app according to the entire config set
kkappkit/run -g /path/to/my_app/my_app.kak.json

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
        '--name',
        action='store',
        dest='name',
        type=str,
        default='',
        required=False,
        help='the name of the target app'
    )
    parser.add_argument(
        '-g',
        '--generate-with-config',
        action='store',
        dest='generateWithConfig',
        type=str,
        default='',
        required=False,
        help='path to app-config file, default to use default location generated by -n'
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
