import argparse

import kkappkit_imp as imp


def main():
    parser = create_parser()
    add_arguments(parser)
    worker = imp.Core(parser.parse_args())
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
# generate empty app project with default app-config under current working directory (cwd)
kkgenapp -n

# generate or update app (except app implementation) after editing app-config
cd /path/to/my_app && kkgenapp

# =============
# REMARKS
# =============
- Add kkappkit folder to your PATH environment variable to run it from anywhere
- Build Variables:
  - {{name}}: the name of the target app
  - {{cli}}: the path to the app's commandline interface script
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
        help='Name of the new app to create'
    )


if __name__ == '__main__':
    main()
