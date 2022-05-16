"""Base class implementation for a package runner"""

# Future
from __future__ import annotations

# Standard Library
import abc
import pathlib
import tempfile
from typing import TYPE_CHECKING, List

# Houdini Package Runner
from houdini_package_runner.config import PackageRunnerConfig

# Imports for type checking.
if TYPE_CHECKING:
    import argparse

    from houdini_package_runner.config import BaseRunnerConfig
    from houdini_package_runner.discoverers.base import BaseItemDiscoverer
    from houdini_package_runner.items.base import BaseItem


# =============================================================================
# CLASSES
# =============================================================================


class HoudiniPackageRunner(abc.ABC):
    """The base package runner class.

    :param discoverer: The item discoverer used by the runner.
    :param write_back: Whether the runner should write the results back.
    :param runner_config: Optional BaseRunnerConfig object.

    """

    def __init__(
        self,
        discoverer: BaseItemDiscoverer,
        write_back: bool = False,
        runner_config: BaseRunnerConfig = None,
    ) -> None:
        self._discoverer = discoverer
        self._extra_args: List[str] = []
        self._hotl_command = "hotl"
        self._list_items = False
        self._temp_dir = pathlib.Path(tempfile.mkdtemp())
        self._verbose = False
        self._write_back = write_back

        if runner_config is None:
            runner_config = PackageRunnerConfig(self.name)

        self._config = runner_config

    # -------------------------------------------------------------------------
    # PROPERTIES
    # -------------------------------------------------------------------------

    @property
    def config(self) -> BaseRunnerConfig:
        """The configuration for the runner."""
        return self._config

    @property
    def discoverer(self) -> BaseItemDiscoverer:
        """The discoverer used by the runner."""
        return self._discoverer

    @property
    def extra_args(self) -> List[str]:
        """A list of extra args to pass to the runner execution."""
        return self._extra_args

    @property
    def hotl_command(self) -> str:
        """The hotl command to use when dealing with digital asset files."""
        return self._hotl_command

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """The runner name used for identification."""

    @property
    def temp_dir(self) -> pathlib.Path:
        """The temp directory used by the package runner."""
        return self._temp_dir

    @property
    def verbose(self) -> bool:
        """Whether to output verbose runner output."""
        return self._verbose

    @property
    def write_back(self) -> bool:
        """Whether the runner should write the results back."""
        return self._write_back

    # -------------------------------------------------------------------------
    # METHODS
    # -------------------------------------------------------------------------

    @abc.abstractmethod
    def process_path(self, file_path: pathlib.Path, item: BaseItem) -> int:
        """Process a file path.

        :param file_path: The path to process.
        :param item: The item to process.
        :return: The process return code.

        """

    def init_args_options(
        self, namespace: argparse.Namespace, extra_args: List[str]
    ):  # pylint: disable=unused-argument
        """Initialize any extra options from parser data.

        :param namespace: Argument parser namespace.
        :param extra_args: Optional list of extra_args to pass to isort.

        """
        self._verbose = namespace.verbose
        self._list_items = namespace.list_items

        if hasattr(namespace, "hotl_command"):
            self._hotl_command = namespace.hotl_command

    def run(self) -> int:
        """Process all the items.

        :return: The overall execution return code.

        """
        if self._list_items:
            for item in self.discoverer.items:
                print(item)

            return 0

        result = 0

        for item in self.discoverer.items:
            if self.write_back:
                item.write_back = True

            result |= item.process(self)

        return result
