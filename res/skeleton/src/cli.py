#
# GENERATED: DO NOT EDIT
#
import argparse
# project
import imp


def main():
    parser = create_parser()
    add_arguments(parser)
    core = imp.Core(parser.parse_args())
    out = core.run()
    send(out)


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
# {{args}}
    pass


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
