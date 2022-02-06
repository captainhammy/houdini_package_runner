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

        command = [
            "python-modernize",
            "--write",
            "--nobackups",
        ]

        command.extend(flags)

        command.append(str(file_path))

        return houdini_package_runner.utils.execute_subprocess_command(
            command, verbose=self._verbose
        )


# =============================================================================
# FUNCTIONS
# =============================================================================

def build_parser() -> argparse.ArgumentParser:
    """Build a parser for the runner.

    :return: The common parser for the runner.

    """
    parser = houdini_package_runner.parser.build_common_parser()

    return parser
