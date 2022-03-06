"""This module contains the definition for a pylint HoudiniPackageRunner."""

# =============================================================================
# IMPORTS
# =============================================================================

# Future
from __future__ import annotations

# Standard Library
import pathlib
import sys
from io import StringIO
from typing import TYPE_CHECKING, List

# Third Party
import termcolor
from pylint import lint
from pylint.reporters.text import ColorizedTextReporter

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


class PyLintRunner(HoudiniPackageRunner):
    """Implementation for a pylint package runner.

    :param discoverer: The item discoverer used by the runner.

    """

    def __init__(
        self,
        discoverer: BaseItemDiscoverer,
    ) -> None:
        super().__init__(discoverer)

        self._disabled: List[str] = []
        self._extra_parts: List[str] = []

    # -------------------------------------------------------------------------
    # PROPERTIES
    # -------------------------------------------------------------------------

    @property
    def extra_parts(self) -> List[str]:
        """A list of extra args to pass to the lint command."""
        return self._extra_parts

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
            "--rcfile",
            action="store",
            default="pylint.rc",
            help="Specify a configuration file",
        )

        parser.add_argument("--disable", action="store", help="Tests to disable.")

        return parser

    def init_args_options(self, namespace: argparse.Namespace, extra_args: List[str]):
        """Initialize any extra options from parser data.

        :param namespace: Argument parser namespace.
        :param extra_args: Optional list of extra_args to pass to isort.

        """
        super().init_args_options(namespace, extra_args)

        if namespace.rcfile:
            extra_args.insert(0, f"--rcfile={namespace.rcfile}")

        if namespace.disable:
            self._disabled = namespace.disable.split(",")

        if extra_args:
            self._extra_parts.extend(extra_args)

    def process_path(self, file_path: pathlib.Path, item: BaseItem) -> bool:
        """Process a file path.

        :param file_path: The path to lint.
        :param item: The item to lint.
        :return: Whether violations were detected.

        """
        flags = []

        flags.extend(self.extra_parts)

        to_disable = []

        if self._disabled:
            to_disable.extend(self._disabled)

        # Many times the 'hou' module is automatically available in the evaluation
        # context so for certain types we want to ignore any undefined variable errors
        # related to it.
        known_builtins: List[str] = []

        if isinstance(self.discoverer, PackageItemDiscoverer):
            known_builtins.extend(item.ignored_builtins)

            if isinstance(item, xml.XMLBase):
                to_disable.extend(
                    [
                        "invalid-name",
                        "missing-final-newline",
                        "missing-module-docstring",
                        "missing-docstring",
                        "return-outside-function",
                    ]
                )

            if isinstance(item, dialog_script.DialogScriptInternalItem):
                to_disable.extend(
                    [
                        "invalid-name",
                        "missing-final-newline",
                        "missing-module-docstring",
                        "return-outside-function",
                    ]
                )

        if known_builtins:
            houdini_package_runner.utils.add_or_append_to_flags(
                flags, "--additional-builtins", known_builtins
            )

        if to_disable:
            flags.append(f"--disable={','.join(to_disable)}")

        buf = StringIO()

        if self.verbose:
            print(
                termcolor.colored(str(item), "cyan"),
                termcolor.colored(" ".join(flags), "magenta"),
            )

        lint.Run(
            [str(file_path)] + flags, reporter=ColorizedTextReporter(buf), exit=False
        )

        stdout = buf.getvalue()

        sys.stdout.write(stdout)

        if self.verbose:
            print()

        return not stdout
