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
from pylint import lint
from pylint.reporters.text import ColorizedTextReporter

# Houdini Package Runner
import houdini_package_runner.config
import houdini_package_runner.parser
import houdini_package_runner.runners.utils
import houdini_package_runner.utils
from houdini_package_runner.discoverers import package
from houdini_package_runner.runners.base import HoudiniPackageRunner

# Imports for type checking.
if TYPE_CHECKING:
    import argparse

    from houdini_package_runner.config import BaseRunnerConfig
    from houdini_package_runner.discoverers.base import BaseItemDiscoverer
    from houdini_package_runner.items.base import BaseItem

# =============================================================================
# CLASSES
# =============================================================================


class PyLintRunner(HoudiniPackageRunner):
    """Implementation for a pylint package runner.

    Args:
        discoverer: The item discoverer used by the runner.
        runner_config: Optional BaseRunnerConfig object.

    """

    def __init__(
        self, discoverer: BaseItemDiscoverer, runner_config: BaseRunnerConfig = None
    ) -> None:
        super().__init__(discoverer, runner_config=runner_config)

        self._disabled: List[str] = []

    # -------------------------------------------------------------------------
    # PROPERTIES
    # -------------------------------------------------------------------------

    @property
    def name(self) -> str:
        """The runner name used for identification."""
        return "pylint"

    # -------------------------------------------------------------------------
    # METHODS
    # -------------------------------------------------------------------------

    @staticmethod
    def build_parser(parser: argparse.ArgumentParser = None) -> argparse.ArgumentParser:
        """Build a parser for the runner.

        Args:
            parser: Optional parser to add arguments to, otherwise a new one will be created.

        Returns:
            The common parser for the runner.

        """
        if parser is None:
            parser = houdini_package_runner.parser.build_common_parser(
                description="""Run pylint on Houdini package items.

Any unknown args will be passed along to the pylint command.
"""
            )

        parser.add_argument(
            "--rcfile",
            action="store",
            help="Specify a configuration file",
        )

        parser.add_argument("--disable", action="store", help="Tests to disable.")

        return parser

    def init_args_options(
        self, namespace: argparse.Namespace, extra_args: List[str]
    ) -> None:
        """Initialize any extra options from parser data.

        Args:
            namespace: Argument parser namespace.
            extra_args: Optional list of extra_args to pass to isort.

        """
        super().init_args_options(namespace, extra_args)

        if namespace.rcfile:
            extra_args.insert(0, f"--rcfile={namespace.rcfile}")

        if namespace.disable:
            self._disabled = namespace.disable.split(",")

        if extra_args:
            self._extra_args.extend(extra_args)

    def process_path(self, file_path: pathlib.Path, item: BaseItem) -> int:
        """Process a file path.

        Args:
            file_path: The path to lint.
            item: The item to lint.

        Returns:
            The process return code.

        """
        flags = []

        flags.extend(self.extra_args)

        to_disable = []

        if self._disabled:
            to_disable.extend(self._disabled)

        to_disable.extend(self.config.get_config_data("to_disable", item, file_path))

        flags.extend(self.config.get_config_data("command", item, file_path))

        known_builtins: List[str] = item.ignored_builtins

        known_builtins.extend(
            self.config.get_config_data("known_builtins", item, file_path)
        )

        if known_builtins:
            houdini_package_runner.utils.add_or_append_to_flags(
                flags, "--additional-builtins", known_builtins
            )

        if to_disable:
            flags.append(f"--disable={','.join(to_disable)}")

        command = flags + [str(file_path)]

        if self.verbose:
            houdini_package_runner.runners.utils.print_runner_command(
                item, command, extra="pylint --output-format=colorized "
            )

        buf = StringIO()

        result = lint.Run(command, reporter=ColorizedTextReporter(buf), exit=False)

        output = buf.getvalue()

        if output:
            sys.stdout.write(output)

        return result.linter.msg_status


# =============================================================================
# FUNCTIONS
# =============================================================================


def main() -> int:
    """Run 'pylint' on package files.

    Returns:
        The runner return code.

    """
    parser = PyLintRunner.build_parser()
    parsed_args, unknown = parser.parse_known_args()

    discoverer = package.init_standard_package_discoverer(parsed_args)

    run_tool = PyLintRunner(discoverer)
    run_tool.init_args_options(parsed_args, unknown)

    result = run_tool.run()
    return result
