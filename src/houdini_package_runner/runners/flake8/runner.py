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


class Flake8Runner(HoudiniPackageRunner):
    """Implementation for a flake8 package runner.

    :param discoverer: The item discoverer used by the runner.
    :param runner_config: Optional BaseRunnerConfig object.

    """

    def __init__(
        self, discoverer: BaseItemDiscoverer, runner_config: BaseRunnerConfig = None
    ) -> None:
        super().__init__(discoverer, write_back=True, runner_config=runner_config)

        self._ignored: List[str] = []

    # -------------------------------------------------------------------------
    # PROPERTIES
    # -------------------------------------------------------------------------

    @property
    def name(self) -> str:
        """The runner name used for identification."""
        return "flake8"

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
            parser = houdini_package_runner.parser.build_common_parser(
                description="""Run flake8 on Houdini package items.

Any unknown args will be passed along to the flake8 command.
"""
            )

        parser.add_argument(
            "--config",
            action="store",
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

    def process_path(self, file_path: pathlib.Path, item: BaseItem) -> int:
        """Process a file path.

        :param file_path: The path to format.
        :param item: The item to format.
        :return: The process return code.

        """
        command = [
            "flake8",
        ]

        to_ignore = []

        if self._ignored:
            to_ignore.extend(self._ignored)

        known_builtins: List[str] = item.ignored_builtins

        to_ignore.extend(self.config.get_config_data("to_ignore", item, file_path))

        command.extend(self.config.get_config_data("command", item, file_path))

        known_builtins.extend(
            self.config.get_config_data("known_builtins", item, file_path)
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


# =============================================================================
# FUNCTIONS
# =============================================================================


def main() -> int:
    """Run 'flake8' on package files.

    :return: The runner return code.

    """
    parser = Flake8Runner.build_parser()

    parsed_args, unknown = parser.parse_known_args()

    discoverer = package.init_standard_package_discoverer(parsed_args)

    run_tool = Flake8Runner(discoverer)
    run_tool.init_args_options(parsed_args, unknown)

    result = run_tool.run()
    return result
