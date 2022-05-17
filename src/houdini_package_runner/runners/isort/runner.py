"""This module contains the definition for an isort package runner."""

# =============================================================================
# IMPORTS
# =============================================================================

# Future
from __future__ import annotations

# Standard Library
import importlib.resources
import os
import pathlib
from configparser import ConfigParser
from typing import TYPE_CHECKING, List, Optional

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


class IsortRunner(HoudiniPackageRunner):
    """Implementation for an isort package runner.

    :param discoverer: The item discoverer used by the runner.
    :param runner_config: Optional BaseRunnerConfig object.

    """

    def __init__(
        self, discoverer: BaseItemDiscoverer, runner_config: BaseRunnerConfig = None
    ) -> None:
        # Set write_back as isort will change files by default.
        super().__init__(discoverer, write_back=True, runner_config=runner_config)

        self._config_file: Optional[str] = None

    def _generate_config(self, namespace: argparse.Namespace):
        """Generate a .isort config file for the operation.

        :param namespace: The command argparse namespace.
        :return: The path to the generated config file.

        """
        config = _load_template_config()

        self._process_config(config, namespace)

        return _save_template_config(config, self.temp_dir)

    def _get_first_party_header(  # pylint: disable=no-self-use
        self, package_names: str
    ) -> str:
        """Get a header for the First Party section.

        This will take the first module name in the comma separated list and use title() on it.

        :param package_names: A comma separated list of first party package names.
        :return: A header name.

        """
        return package_names.split(",")[0].replace("_", " ").title()

    def _get_first_party_packages(self, namespace: argparse.Namespace) -> Optional[str]:
        """Find a list of known first party module names, if any.

        :param namespace: The command argparse namespace.
        :return: A comma separated list of first party names, otherwise None.

        """
        first_party_packages = None

        if namespace.package_names is not None:
            first_party_packages = namespace.package_names

        # If no first party package names were passed we can try and figure out any
        # based on the Python root.
        elif namespace.python_root is not None:
            python_root = self.discoverer.path / namespace.python_root

            if python_root.exists():
                first_party_packages = _find_python_packages_from_path(python_root)

        return first_party_packages

    def _get_houdini_names(  # pylint: disable=no-self-use
        self, namespace: argparse.Namespace
    ) -> str:
        """Find a list of known Houdini shipped module names.

        :param namespace: The command argparse namespace.
        :return: A comma separated list of Houdini Python modules.

        """
        hfs_path = pathlib.Path(os.path.expandvars(namespace.hfs_path))

        return ",".join(_find_known_houdini(hfs_path))

    def _process_config(
        self,
        config: ConfigParser,
        namespace: argparse.Namespace,
    ):
        """Process the ConfigParser object.

        :param config: The configuration object.
        :param namespace: The command argparse namespace.
        :return:

        """
        settings = config["settings"]

        settings["known_houdini"] = self._get_houdini_names(namespace)

        first_party_packages = self._get_first_party_packages(namespace)

        if first_party_packages is not None:
            settings["known_first_party"] = first_party_packages

            settings["import_heading_firstparty"] = self._get_first_party_header(
                first_party_packages
            )

    # -------------------------------------------------------------------------
    # PROPERTIES
    # -------------------------------------------------------------------------

    @property
    def config_file(self) -> Optional[str]:
        """Optional isort config file."""
        return self._config_file

    @config_file.setter
    def config_file(self, setting_file: str):
        self._config_file = setting_file

    # -------------------------------------------------------------------------

    @property
    def name(self) -> str:
        """The runner name used for identification."""
        return "isort"

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
                description="""Run isort on Houdini package items.

Any unknown args will be passed along to the isort command.
"""
            )

        parser.add_argument(
            "--config-file",
            action="store",
            default=".isort.cfg",
            help="Optional config file to pass to isort commands",
        )

        parser.add_argument(
            "--hfs-path",
            action="store",
            default="$HFS",
            help="Path to a Houdini install directory for known Houdini modules",
        )

        parser.add_argument(
            "--package-names", action="store", help="Known first party package names"
        )

        return parser

    def init_args_options(self, namespace: argparse.Namespace, extra_args: List[str]):
        """Initialize any extra options from parser data.

        :param namespace: Argument parser namespace.
        :param extra_args: Optional list of extra_args to pass to isort.

        """
        super().init_args_options(namespace, extra_args)

        config_file = namespace.config_file

        if config_file is not None:
            if (self.discoverer.path / config_file).exists():
                self.config_file = self.discoverer.path / config_file

        self._extra_args = extra_args

        # If the check flag was passed as an extra arg then disable write_back as it
        # will just cause unnecessary extra work.
        if "--check" in extra_args:
            self._write_back = False

        if self.config_file is None:
            self.config_file = self._generate_config(namespace)

    def process_path(self, file_path: pathlib.Path, item: BaseItem) -> int:
        """Process a file path.

        :param file_path: The path to format.
        :param item: The item to format.
        :return: The process return code.

        """
        command = [
            "isort",
        ]

        if self.config_file is not None:
            command.extend(("--sp", str(self.config_file)))

        command.extend(self.extra_args)

        command.append(str(file_path))

        return houdini_package_runner.utils.execute_subprocess_command(
            command, verbose=self._verbose
        )


# =============================================================================
# NON-PUBLIC FUNCTIONS
# =============================================================================


def _find_known_houdini(hfs_path: pathlib.Path) -> List[str]:
    """Find a list of known Houdini Python modules.

    :param hfs_path: The path to a Houdini install directory ($HFS)
    :return: A list of Houdini module names.

    """
    module_names = []

    python_libs_paths = (hfs_path / "houdini").glob("python*libs")

    for path in python_libs_paths:
        module_names.extend(_find_python_modules(path))

    soho_paths = (hfs_path / "houdini" / "soho").glob("python*")

    for path in soho_paths:
        module_names.extend(_find_python_modules(path))

    return sorted(set(module_names))


def _find_python_modules(folder: pathlib.Path) -> List[str]:
    """Find modules in a directory.

    :param folder: The directory to look for Python modules in.
    :return: A list of Python module names.

    """
    module_names = []

    for child in folder.iterdir():
        if child.is_file() and child.suffix in (".py", ".so"):
            module_names.append(child.stem)

        elif child.is_dir() and not child.stem.startswith("__"):
            module_names.append(child.stem)

    return sorted(module_names)


def _find_python_packages_from_path(search_root: pathlib.Path) -> Optional[str]:
    """Attempt to find any Python package names under the search path.

    :param search_root: The path to search under.
    :return: Any found package names.

    """
    package_names = []

    # Check for any folders under the root.
    for path in search_root.iterdir():
        if path.is_dir() and (path / "__init__.py").exists():
            package_names.append(path.stem)

    return ",".join(sorted(package_names)) if package_names else None


def _load_template_config() -> ConfigParser:
    """Load the template config file.

    :return: The loaded default config file.

    """
    config = ConfigParser()

    with importlib.resources.open_text(
        "houdini_package_runner.runners.isort", "isort.cfg"
    ) as contents:
        config.read_file(contents)

    return config


def _save_template_config(config: ConfigParser, temp_dir: pathlib.Path):
    """Save the config to a temporary file for running.

    :param config: The configuration to save.
    :param temp_dir: The runner temporary directory.
    :return: The saved configuration file path.

    """
    file_path = temp_dir / ".isort.cfg"

    with open(file_path, "w", encoding="utf-8") as handle:
        config.write(handle)

    return file_path


# =============================================================================
# FUNCTIONS
# =============================================================================


def main() -> int:
    """Run 'isort' on package files.

    :return: The runner return code.

    """
    parser = IsortRunner.build_parser()

    parsed_args, unknown = parser.parse_known_args()

    discoverer = package.init_standard_package_discoverer(parsed_args)

    run_tool = IsortRunner(discoverer)
    run_tool.init_args_options(parsed_args, unknown)

    result = run_tool.run()
    return result
