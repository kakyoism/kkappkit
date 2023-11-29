#
# GENERATED: DO NOT EDIT
#
import argparse
import os.path as osp
# project
import impl


def main():
    parser = create_parser()
    add_arguments(parser)
    core = impl.Core(parser.parse_args())
    out = core.run()
    send(out)


def file(path):
    """
    - must resolve path in implementation for following:
      - empty string: valid path placeholder
      - string containing $VAR$: cross-platform standard folders
    """
    if path and '$' not in path and not osp.isfile(path):
        raise argparse.ArgumentTypeError(f"invalid file path argument: {path}; Does it exist?")
    return path


def folder(path):
    if path and '$' not in path and not osp.isdir(path):
        raise argparse.ArgumentTypeError(f"invalid folder path argument: {path}; Does it exist?")
    return path


def ranged_float(min_val, max_val):
    """ Factory function to generate range checking functions for argparse """

    def check_range(value):
        try:
            val = float(value)
        except ValueError:
            raise argparse.ArgumentTypeError(f"Must be a floating point number, got '{value}'")

        if val < min_val or val > max_val:
            raise argparse.ArgumentTypeError(f"Must be in range [{min_val}, {max_val}], got '{val}'")

        return val

    return check_range


def ranged_int(min_val, max_val):
    """ Factory function to generate range checking functions for argparse """

    def check_range(value):
        try:
            val = int(value)
        except ValueError:
            raise argparse.ArgumentTypeError(f"Must be an integer, got '{value}'")

        if val < min_val or val > max_val:
            raise argparse.ArgumentTypeError(f"Must be in range [{min_val}, {max_val}], got '{val}'")

        return val

    return check_range


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
