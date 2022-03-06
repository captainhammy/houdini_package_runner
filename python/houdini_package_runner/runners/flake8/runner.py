"""This module contains the definition for an flake8 package runner."""

# =============================================================================
# IMPORTS
# =============================================================================

# Future
from __future__ import annotations

# Standard Library
import pathlib
from typing import TYPE_CHECKING, List

# Houdini Package Runner
import houdini_package_runner.parser
import houdini_package_runner.utils
from houdini_package_runner.discoverers.package import PackageItemDiscoverer
from houdini_package_runner.items import dialog_script, xml
from houdini_package_runner.runners.base import HoudiniPackageRunner

# Imports for type checking.
if TYPE_CHECKING:
    import argparse

    from houdini_package_runner.discoverers.base import BaseItemDiscoverer
    from houdini_package_runner.items.base import BaseItem


# =============================================================================
# CLASSES
# =============================================================================


class Flake8Runner(HoudiniPackageRunner):
    """Implementation for a flake8 package runner.

    :param discoverer: The item discoverer used by the runner.

    """

    def __init__(self, discoverer: BaseItemDiscoverer) -> None:
        super().__init__(discoverer, write_back=True)

        self._ignored: List[str] = []
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

        parser.add_argument(
            "--config",
            action="store",
            default=".flake8",
            help="Specify a configuration file",
        )

        parser.add_argument("--ignore", action="store", help="Tests to ignore.")

        return parser

    def init_args_options(self, namespace: argparse.Namespace, extra_args: List[str]):
        """Initialize any extra options from parser data.

        :param namespace: Argument parser namespace.
        :param extra_args: Optional list of extra_args to pass to isort.

        """
        super().init_args_options(namespace, extra_args)

        if namespace.config:
            extra_args.insert(0, f"--config={namespace.config}")

        if namespace.ignore:
            self._ignored = namespace.ignore.split(",")

        self._extra_args = extra_args

    def process_path(self, file_path: pathlib.Path, item: BaseItem) -> bool:
        """Process a file path.

        :param file_path: The path to format.
        :param item: The item to format.
        :return: Whether the black was successful.

        """
        command = [
            "flake8",
        ]

        to_ignore = []

        if self._ignored:
            to_ignore.extend(self._ignored)

        known_builtins: List[str] = item.ignored_builtins

        if isinstance(self.discoverer, PackageItemDiscoverer):
            if isinstance(item, xml.XMLBase):
                command.append("--max-line-length=150")

                to_ignore.extend(
                    [
                        "W292",  # No newline at end of file
                    ]
                )

            if isinstance(item, dialog_script.DialogScriptInternalItem):
                to_ignore.extend(
                    [
                        "W292",  # No newline at end of file
                        "F706",  # 'return' outside function
                    ]
                )

        if known_builtins:
            houdini_package_runner.utils.add_or_append_to_flags(
                command, "--builtins", known_builtins
            )

        if to_ignore:
            command.append(f"--ignore={','.join(to_ignore)}")

        command.extend(self.extra_args)

        command.append(str(file_path))

        return houdini_package_runner.utils.execute_subprocess_command(
            command, verbose=self._verbose
        )
