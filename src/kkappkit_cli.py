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
kkgenapp -n my_app

# same as above, but use a different app-config template, i.e., filename without extension
kkgenapp -n my_app -t my_template

# generate or update app (except app implementation) after editing app-config
cd /path/to/my_app && kkgenapp

# =============
# REMARKS
# =============
- Add kkappkit folder to your PATH environment variable to run it from anywhere
- Templates are under kkappkit/template
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
        required=False,
        help='Name of the new app to create'
    )
    parser.add_argument(
        '-t',
        '--app-template',
        action='store',
        choices=('offline', 'rt'),
        dest='appTemplate',
        default='offline',
        type=str,
        required=False,
        help='App-config template for creating the new app'
    )


if __name__ == '__main__':
    main()
