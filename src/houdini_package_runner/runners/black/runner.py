"""This module contains the definition for a black HoudiniPackageRunner."""

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
from houdini_package_runner.runners.base import HoudiniPackageRunner

# Imports for type checking.
if TYPE_CHECKING:
    import argparse
    import pathlib

    from houdini_package_runner.config import BaseRunnerConfig
    from houdini_package_runner.discoverers.base import BaseItemDiscoverer
    from houdini_package_runner.items.base import BaseItem


# =============================================================================
# CLASSES
# =============================================================================


class BlackRunner(HoudiniPackageRunner):
    """Implementation for a black package runner.

    :param discoverer: The item discoverer used by the runner.
    :param runner_config: Optional BaseRunnerConfig object.

    """

    def __init__(
        self, discoverer: BaseItemDiscoverer, runner_config: BaseRunnerConfig = None
    ) -> None:
        # Set write_back as black will change files by default.
        super().__init__(discoverer, write_back=True, runner_config=runner_config)

    # -------------------------------------------------------------------------
    # PROPERTIES
    # -------------------------------------------------------------------------

    @property
    def name(self) -> str:
        """The runner name used for identification."""
        return "black"

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
                description="""Run black on Houdini package items.

Any unknown args will be passed along to the black command.
"""
            )

        return parser

    def init_args_options(self, namespace: argparse.Namespace, extra_args: List[str]):
        """Initialize any extra options from parser data.

        :param namespace: Argument parser namespace.
        :param extra_args: Optional list of extra_args to pass to isort.

        """
        super().init_args_options(namespace, extra_args)

        self._extra_args = extra_args

        # If the check flag was passed as an extra arg then disable write_back as it
        # will just cause unnecessary extra work.
        if "--check" in extra_args:
            self._write_back = False

    def process_path(self, file_path: pathlib.Path, item: BaseItem) -> int:
        """Process a file path.

        :param file_path: The path to format.
        :param item: The item to format.
        :return: The process return code.

        """
        flags = []

        flags.extend(self.config.get_config_data("flags", item, file_path))

        flags.extend(self.extra_args)

        command = [
            "black",
        ]

        # Set the target Python version if not passed via flags.
        if not any("target-version" in flag for flag in flags):
            command.append("--target-version=py37")

        command.extend(flags)

        command.append(str(file_path))

        return houdini_package_runner.utils.execute_subprocess_command(
            command, verbose=self._verbose
        )


# =============================================================================
# FUNCTIONS
# =============================================================================


def main() -> int:
    """Run 'black' on package files.

    :return: The runner return code.

    """
    parser = BlackRunner.build_parser()

    parsed_args, unknown = parser.parse_known_args()

    discoverer = package.init_standard_package_discoverer(parsed_args)

    run_tool = BlackRunner(discoverer)
    run_tool.init_args_options(parsed_args, unknown)

    result = run_tool.run()

    return result
