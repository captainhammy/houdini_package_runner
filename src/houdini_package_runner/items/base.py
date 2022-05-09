"""This module contains a base runnable item."""

# =============================================================================
# IMPORTS
# =============================================================================

# Future
from __future__ import annotations

# Standard Library
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List

# Imports for type checking.
if TYPE_CHECKING:
    import pathlib

    import houdini_package_runner.runners.base


# =============================================================================
# CLASSES
# =============================================================================


class BaseItem(ABC):
    """Base class for a runnable item.

    :param write_back: Whether the item should write itself back to disk.

    """

    def __init__(self, write_back: bool = False) -> None:
        self._contents_changed = False
        self._ignored_builtins: List[str] = []
        self._is_single_line = False
        self._is_test_item = False
        self._write_back = write_back

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    # -------------------------------------------------------------------------
    # PROPERTIES
    # -------------------------------------------------------------------------

    @property
    def contents_changed(self) -> bool:
        """Whether the contents of the item have changed."""
        return self._contents_changed

    @contents_changed.setter
    def contents_changed(self, contents_changed: bool):
        self._contents_changed = contents_changed

    # -------------------------------------------------------------------------

    @property
    def ignored_builtins(self) -> List[str]:
        """A list of known builtins to ignore for checks which look for imports."""
        return self._ignored_builtins

    # -------------------------------------------------------------------------

    @property
    def is_single_line(self) -> bool:
        """Whether the item code on a single line."""
        return self._is_single_line

    # -------------------------------------------------------------------------

    @property
    def is_test_item(self) -> bool:
        """Whether the item is a test related item."""
        return self._is_test_item

    @is_test_item.setter
    def is_test_item(self, is_test_item: bool):
        self._is_test_item = is_test_item

    # -------------------------------------------------------------------------

    @property
    def write_back(self) -> bool:
        """Whether the item should write changes back."""
        return self._write_back

    @write_back.setter
    def write_back(self, write_back):
        self._write_back = write_back

    # -------------------------------------------------------------------------
    # METHODS
    # -------------------------------------------------------------------------

    @abstractmethod
    def process(
        self, runner: houdini_package_runner.runners.base.HoudiniPackageRunner
    ) -> int:
        """Process an item.

        :param runner: The package runner processing the item.
        :return: The process return code.

        """


class BaseFileItem(BaseItem):
    """Base class for a runnable item.

    :param path: The path for the item.
    :param write_back: Whether the item should write itself back to disk.

    """

    def __init__(self, path: pathlib.Path, write_back: bool = False) -> None:
        super().__init__(write_back=write_back)
        self._path = path

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.path}>"

    # -------------------------------------------------------------------------
    # PROPERTIES
    # -------------------------------------------------------------------------

    @property
    def path(self) -> pathlib.Path:
        """The path on disk."""
        return self._path

    # -------------------------------------------------------------------------
    # METHODS
    # -------------------------------------------------------------------------

    @abstractmethod
    def process(
        self, runner: houdini_package_runner.runners.base.HoudiniPackageRunner
    ) -> int:
        """Process an item.

        :param runner: The package runner processing the item.
        :return: The process return code.

        """
