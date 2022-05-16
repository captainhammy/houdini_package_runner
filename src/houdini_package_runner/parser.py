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
# CLASSES
# =============================================================================


class _UltimateHelpFormatter(
    argparse.RawTextHelpFormatter, argparse.ArgumentDefaultsHelpFormatter
):
    """Formatter class that combines RawTextHelpFormatter and ArgumentDefaultsHelpFormatter."""


# =============================================================================
# NON-PUBLIC FUNCTIONS
# =============================================================================


def _resolve_houdini_root(
    parsed_args: argparse.Namespace, root: pathlib.Path
) -> pathlib.Path:
    """Resolve the Houdini root from the args and path.

    :param parsed_args: The parsed command args.
    :param root: The root path.
    :return: The resolved Houdini root.

    """
    if parsed_args.houdini_root is not None:
        houdini_root_value = parsed_args.houdini_root

        if pathlib.Path(houdini_root_value).is_dir():
            return pathlib.Path(houdini_root_value)

        if (root / houdini_root_value).is_dir():
            return root / houdini_root_value

        raise OSError("Could not find houdini root")

    if (root / "houdini").is_dir():
        houdini_root = root / "houdini"

    else:
        houdini_root = root

    return houdini_root


def _resolve_python_packages(
    parsed_args: argparse.Namespace, root: pathlib.Path
) -> List[pathlib.Path]:
    """Find any Python package paths from the args and path.

    :param parsed_args: The parsed command args.
    :param root: The root path.
    :return: A list of any found Python package directories.

    """
    if parsed_args.python_root:
        python_dir = root / parsed_args.python_root

        if python_dir.is_dir():
            return [python_dir]

    return []


def _resolve_tests(
    parsed_args: argparse.Namespace, root: pathlib.Path
) -> List[pathlib.Path]:
    """Find any test paths from the args and path.

    :param parsed_args: The parsed command args.
    :param root: The root path.
    :return: A list of any test directories.

    """
    directories = []

    if not parsed_args.skip_tests:
        test_dir = root / "tests"

        if test_dir.is_dir():
            directories.append(test_dir)

    return directories


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
        formatter_class=_UltimateHelpFormatter,
    )

    parser.add_argument(
        "--add-dir",
        action="append",
        dest="directories",
        default=[],
        help="Add a directory to be processed",
    )

    parser.add_argument(
        "--add-file",
        action="append",
        dest="files",
        default=[],
        help="Add a file to be processed",
    )

    parser.add_argument(
        "--houdini-items",
        action="store",
        default="otls,hda,toolbar,python_panels,pythonXlibs,scripts,soho,menus",
        help="A list of Houdini items to process",
    )

    parser.add_argument(
        "--houdini-root",
        action="store",
        help="The root directory that the Houdini items will be in",
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

    parser.add_argument(
        "--list-items",
        action="store_true",
        help="Only list the found items and do not execute the runner.",
    )

    return parser


def process_common_arg_settings(
    parsed_args: argparse.Namespace,
) -> Tuple[pathlib.Path, pathlib.Path, List[pathlib.Path], List[str]]:
    """Generate base settings from common command args.

    :param parsed_args: The parsed command args.
    :return: The root path, houdini root path, directories and files to process, and Houdini item names.

    """
    if parsed_args.root:
        root = pathlib.Path(parsed_args.root)

    else:
        root = pathlib.Path.cwd()

    houdini_root = _resolve_houdini_root(parsed_args, root)

    extra_paths = [root / dir_name for dir_name in parsed_args.directories]

    extra_paths.extend(_resolve_python_packages(parsed_args, root))

    extra_paths.extend(_resolve_tests(parsed_args, root))

    extra_paths.extend([root / file_name for file_name in parsed_args.files])

    houdini_items = parsed_args.houdini_items.split(",")

    return root, houdini_root, extra_paths, houdini_items
