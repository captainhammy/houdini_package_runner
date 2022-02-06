"""This module contains a class to discover package items."""

# =============================================================================
# IMPORTS
# =============================================================================

# Future
from __future__ import annotations

# Standard Library
import argparse
import pathlib
from typing import List, Tuple

# =============================================================================
# FUNCTIONS
# =============================================================================


def build_common_parser(
    prog: str = None, usage: str = None, description: str = None
) -> argparse.ArgumentParser:
    """Build an argument parser for the script args.

    :param prog: The name of the program (default: sys.argv[0])
    :param usage: The string describing the program usage (default: generated from arguments added to parser)
    :param description: Text to display before the argument help.
    :return: The constructed parser.

    """
    parser = argparse.ArgumentParser(
        prog=prog,
        usage=usage,
        description=description,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--add-dir",
        action="append",
        dest="directories",
        default=[],
        help="Add a directory to be modernized",
    )

    parser.add_argument(
        "--add-file",
        action="append",
        dest="files",
        default=[],
        help="Add a file to be modernized",
    )

    parser.add_argument(
        "--houdini-items",
        action="store",
        default="otls,toolbar,python_panels,python2.7libs,python3.7libs,scripts,soho,menus",
        help="A list of Houdini items to lint",
    )

    parser.add_argument(
        "--python-root",
        action="store",
        default="python",
        help="The root directory the package will be in",
    )

    parser.add_argument(
        "--root",
        action="store",
        help="Optional root directory to look for things from.  By default uses the cwd",
    )

    parser.add_argument("--verbose", action="store_true", help="Engage verbose output.")

    parser.add_argument("--hotl-command", action="store", default="hotl")

    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip processing of files under {root}/tests.",
    )

    return parser


def process_common_arg_settings(
    parsed_args: argparse.Namespace,
) -> Tuple[pathlib.Path, List[pathlib.Path], List[pathlib.Path], List[str]]:
    """Generate base settings from common command args.

    :param parsed_args: The parsed command args.
    :return: The root path, directories and files to process, and Houdini item names.

    """
    if parsed_args.root is not None:
        root = pathlib.Path(parsed_args.root)
    else:
        root = pathlib.Path.cwd()

    dirs = [root / dir_name for dir_name in parsed_args.directories]

    if parsed_args.python_root is not None:
        dirs.append(root / parsed_args.python_root)

    if not parsed_args.skip_tests:
        test_dir = root / "tests"

        if test_dir.is_dir():
            dirs.append(test_dir)

    files = [root / file_name for file_name in parsed_args.files]
    houdini_items = parsed_args.houdini_items.split(",")

    return root, dirs, files, houdini_items
