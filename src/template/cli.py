import argparse

import {{app_core}} as core


def main():
    parser = create_parser()
    add_arguments(parser)
    worker = core.Core(parser.parse_args())
    worker.main()


def create_parser():
    return argparse.ArgumentParser(
        prog='{{name}}',
        description='{{description}}',
        add_help=True,
        epilog="""\
# =============
# TUTORIAL
# =============
{{tutorial}}

# =============
# REMARKS
# =============
{{remarks}}
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
        help='the name of the target app'
    )
    parser.add_argument(
        '-p',
        '--parent-folder',
        action='store',
        dest='parDir',
        type=str,
        default='.',
        required=False,
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
