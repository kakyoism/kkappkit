import argparse
# project
import imp as imp


def main():
    parser = create_parser()
    add_arguments(parser)
    core = imp.Core(parser.parse_args())
    out = core.run()
    send(out)


def create_parser():
    return argparse.ArgumentParser(
        prog='kkappkit',
        description='Code-generator for building small tool applications with Python and Tkinter',
        add_help=True,
        epilog="""\
# =============
# EXAMPLES
# =============
# generate empty app project with default app-config under specified root folder if it does not exists
# regenerate its interface (cli, gui, etc.) if it exists 
kkgenapp -p /path/to/my_app

# same as above, but use a different app-config template, i.e., filename without extension
kkgenapp -p my_app -t my_template

# same as above, but force overwrite existing app folder with new one
kkgenapp -p my_app -t my_template -f


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
        '-r',
        '--app-root',
        action='store',
        dest='appRoot',
        type=str,
        default='',
        required=True,
        help='Path to the root folder of the new app to create'
    )
    parser.add_argument(
        '-t',
        '--app-template',
        action='store',
        choices=('form', 'realtime', 'custom'),
        dest='appTemplate',
        default='form',
        type=str,
        required=False,
        help='App-config template that the the new app is based upon; ignored if an app-config already exists'
    )
    parser.add_argument(
        '-f',
        '--force-overwrite',
        action='store_true',
        dest='forceOverwrite',
        default=False,
        required=False,
        help='Force overwrite existing app folder with new one'
    )


def send(out: dict):
    """
    - extract out as json msg and send via stdout
    - out must contain only json-serializable data
    - downstream can receive via stdin and load as json msg
    """
    if not out:
        return
    print(f"""
<<<{out}>>>
""")


if __name__ == '__main__':
    main()
