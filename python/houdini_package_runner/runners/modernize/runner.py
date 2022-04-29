"""This module contains the definition for a python-modernize package runner."""

# =============================================================================
# IMPORTS
# =============================================================================

# Future
from __future__ import annotations

# Standard Library
from typing import TYPE_CHECKING, List

# Houdini Package Runner
import houdini_package_runner.parser
import houdini_package_runner.utils
from houdini_package_runner.discoverers import package
from houdini_package_runner.items.dialog_script import DialogScriptInternalItem
from houdini_package_runner.runners.base import HoudiniPackageRunner

# Imports for type checking.
if TYPE_CHECKING:
    import argparse
    import pathlib

    from houdini_package_runner.discoverers.package import PackageItemDiscoverer
    from houdini_package_runner.items.base import BaseItem


# =============================================================================
# CLASSES
# =============================================================================


class ModernizeRunner(HoudiniPackageRunner):
    """Implementation for a python-modernize package runner.

    :param discoverer: The item discoverer used by the runner.

    """

    def __init__(
        self,
        discoverer: PackageItemDiscoverer,
    ) -> None:
        super().__init__(discoverer, write_back=True)
        self._extra_args: List[str] = []

    # -------------------------------------------------------------------------
    # PROPERTIES
    # -------------------------------------------------------------------------

    @property
    def extra_args(self) -> List[str]:
        """A list of extra args to pass to the format command."""
        return self._extra_args

    # -------------------------------------------------------------------------
    # METHODS
    # -------------------------------------------------------------------------

    @staticmethod
    def build_parser(parser: argparse.ArgumentParser = None) -> argparse.ArgumentParser:
        """Build a parser for the runner.
        :param parser: Optional parser to add arguments to, otherwise a new one will be created.
        :return: The common parser for the runner.

        """
        if parser is None:
            parser = houdini_package_runner.parser.build_common_parser()

        return parser

    def init_args_options(self, namespace: argparse.Namespace, extra_args: List[str]):
        """Initialize any extra options from parser data.

        :param namespace: Argument parser namespace.
        :param extra_args: Optional list of extra_args to pass to isort.

        """
        super().init_args_options(namespace, extra_args)

        self._extra_args = extra_args

    def process_path(self, file_path: pathlib.Path, item: BaseItem) -> bool:
        """Process a file path.

        :param file_path: The path to format.
        :param item: The item to format.
        :return: Whether the black was successful.

        """
        flags = []

        flags.extend(self.extra_args)

        skip_fixers = []

        # Don't want to run the import or print fixers.  The print one is already automatically
        # imported by Houdini and the import one is not necessary as there are no relative imports
        # and because of Houdini's bootstrapping will result in it complaining that __future__ imports
        # are not on the first line.
        if isinstance(item, DialogScriptInternalItem):
            skip_fixers.extend(["import", "print"])

        command = [
            "python-modernize",
            "--write",
            "--nobackups",
        ]

        if skip_fixers:
            houdini_package_runner.utils.add_or_append_to_flags(
                flags, "--nofix", skip_fixers
            )

        command.extend(flags)

        command.append(str(file_path))

        return houdini_package_runner.utils.execute_subprocess_command(
            command, verbose=self._verbose
        )


# =============================================================================
# FUNCTIONS
# =============================================================================


def main() -> None:
    """Run 'python-modernize' on package files."""
    parser = ModernizeRunner.build_parser()

    parsed_args, unknown = parser.parse_known_args()

    discoverer = package.init_standard_discoverer(parsed_args)

    run_tool = ModernizeRunner(discoverer)
    run_tool.init_args_options(parsed_args, unknown)

    run_tool.run()
