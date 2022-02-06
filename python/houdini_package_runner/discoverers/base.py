"""This module contains a class to discover package items."""

# =============================================================================
# IMPORTS
# =============================================================================

# Future
from __future__ import annotations

# Standard Library
import abc
import pathlib
from typing import TYPE_CHECKING, List, Optional

# Imports for type checking.
if TYPE_CHECKING:
    from houdini_package_runner.items.base import BaseItem


# =============================================================================
# CLASSES
# =============================================================================


class BaseItemDiscoverer(metaclass=abc.ABCMeta):
    """This class is responsible for searching for various items to process.

    :param path: The path to start searching for items from.
    :param items: Optional list of specific items to check.

    """

    def __init__(
        self,
        path: pathlib.Path,
        items: Optional[List[BaseItem]] = None,
    ) -> None:
        self._items = [] if items is None else items
        self._path = path

    # -------------------------------------------------------------------------
    # PROPERTIES
    # -------------------------------------------------------------------------

    @property
    def items(self) -> List[BaseItem]:
        """The list of found items for processing."""
        return self._items

    @property
    def path(self) -> pathlib.Path:
        """The root path."""
        return self._path

    # -------------------------------------------------------------------------
    # METHODS
    # -------------------------------------------------------------------------

    def post_run(self) -> None:
        """Optionally perform any operations after running."""
