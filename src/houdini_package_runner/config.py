"""Functioned related to configuration of houdini_package_runner."""

# Future
from __future__ import annotations

# Standard Library
import abc
import importlib.resources
import os
import pathlib
from typing import TYPE_CHECKING, Dict, List, Tuple

# Third Party
import deepmerge
import toml

# Imports for type checking.
if TYPE_CHECKING:
    from houdini_package_runner.items.base import BaseItem


# =============================================================================
# CLASSES
# =============================================================================


class BaseRunnerConfig(abc.ABC):
    """Base class for runner configuration."""

    def __init__(self, runner_name: str):
        self._runner_name = runner_name
        self._data = self.load_config()

    # -------------------------------------------------------------------------
    # PROPERTIES
    # -------------------------------------------------------------------------

    @property
    def data(self) -> dict:
        """The configuration data."""
        return self._data

    @property
    def runner_name(self) -> str:
        """The runner name."""
        return self._runner_name

    # -------------------------------------------------------------------------
    # METHODS
    # -------------------------------------------------------------------------

    @abc.abstractmethod
    def get_config_data(
        self,
        key: str,
        item: BaseItem,
        file_path: pathlib.Path,
    ) -> List:
        """Get config data for an item, and it's file path.

        :param key: The data key.
        :param item: The item to get config data for.
        :param file_path: The item file path to get config data for.
        :return: Any found config data.

        """

    @abc.abstractmethod
    def load_config(self) -> dict:
        """Load the configuration data.

        :return: Any found config data.

        """


class PackageRunnerConfig(BaseRunnerConfig):
    """Config class for default runners.

    This uses the shipped runners.toml file

    """

    # -------------------------------------------------------------------------
    # NON-PUBLIC METHODS
    # -------------------------------------------------------------------------

    def _get_file_config_data(self, file_path: pathlib.Path, key: str) -> List:
        """Get config data based on the file name.

        :param file_path: The file path to get config data for.
        :param key: The data key.
        :return: Any found config data.

        """
        data = []

        file_config = self.data.get("file", {})

        for file_name, file_options in file_config.items():
            if file_name == file_path.name:
                data.extend(file_options.get(key, []))

        return data

    def _get_item_config_data(self, item: BaseItem, key: str) -> List:
        """Get config data based on an item.

        :param item: The item to get config data for.
        :param key: The data key.
        :return: Any found config data.

        """
        config_names = build_config_item_list(item)

        data = []

        item_config = self.data.get("item", {})

        for config_name in config_names:
            config_items = item_config.get(config_name, {})
            data.extend(config_items.get(key, []))

        if item.is_test_item:
            test_items = item_config.get("test_item", {})
            data.extend(test_items.get(key, []))

        return data

    # -------------------------------------------------------------------------
    # METHODS
    # -------------------------------------------------------------------------

    def get_config_data(
        self,
        key: str,
        item: BaseItem,
        file_path: pathlib.Path,
    ) -> List:
        """Get config data for an item, and it's file path.

        :param key: The data key.
        :param item: The item to get config data for.
        :param file_path: The item file path to get config data for.
        :return: Any found config data.

        """
        data = []

        data.extend(self._get_item_config_data(item, key))
        data.extend(self._get_file_config_data(file_path, key))

        return data

    def load_config(self) -> dict:
        """Load the configuration data.

        :return: Any found config data.

        """
        return _load_default_runner_config(self.runner_name)


# =============================================================================
# NON-PUBLIC FUNCTIONS
# =============================================================================


def _find_config_files() -> List[pathlib.Path]:
    """Find any config files to read.

    This uses HOUDINI_PACKAGE_RUNNER_CONFIG_PATH to find any specified config files,
    otherwise it will return the packaged resource.

    :return: One or more config files.

    """
    path_env = os.getenv("HOUDINI_PACKAGE_RUNNER_CONFIG_PATH")

    # Load the packaged config file if none is specified.
    if path_env is None:
        with importlib.resources.path("houdini_package_runner", "runners.toml") as path:
            paths = [path]

    else:
        path_components = path_env.split(os.path.pathsep)

        paths = [
            pathlib.Path(component)
            for component in path_components
            if os.path.exists(component)
        ]

    return paths


def _get_base_classes(cls: type) -> List[type]:
    """Get a list of all the base classes of a class.

    This will exclude the base "object" class.

    :param cls: The class to get the base classes for.
    :return: A list of all the base classes.

    """
    bases = [base for base in cls.__bases__ if not base == object]

    for base in bases:
        bases.extend(_get_base_classes(base))

    return bases


def _load_default_runner_config(runner_name: str) -> dict:
    """Load the configuration for a runner.

    :param runner_name: The name of the runner.
    :return: The configuration dictionary for the runner.

    """
    paths = _find_config_files()

    data: Dict = {}

    # In the event of multiple files, process them all and do a deep merge, preferring
    # data already found over new values in the event of collision.
    for path in paths:
        with path.open("r", encoding="utf-8") as handle:
            path_data = toml.load(handle)
            deepmerge.conservative_merger.merge(data, path_data)

    return data.get(runner_name, {})


# =============================================================================
# FUNCTIONS
# =============================================================================


def build_config_item_list(item: BaseItem) -> Tuple[str, ...]:
    """Build a list of the item's class and super class names.

    :param item: The item to get class names for.
    :return: A list containing the item's class name as well as any super class names.

    """
    bases = [base.__name__ for base in _get_base_classes(type(item))]

    names = [type(item).__name__] + bases

    return tuple(names)
