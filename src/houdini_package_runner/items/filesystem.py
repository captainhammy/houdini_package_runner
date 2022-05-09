"""This module contains runnable items related to entities on disk."""

# =============================================================================
# IMPORTS
# =============================================================================

# Future
from __future__ import annotations

# Standard Library
import hashlib
import pathlib
from typing import TYPE_CHECKING, List, Optional

# Houdini Package Runner
from houdini_package_runner.items.base import BaseFileItem

# Imports for type checking.
if TYPE_CHECKING:
    import houdini_package_runner.runners.base
    from houdini_package_runner.items.base import BaseItem


# =============================================================================
# CLASSES
# =============================================================================


class DirectoryToProcess(BaseFileItem):
    """Class representing a directory to be processed.

    :param path: The path for the item.
    :param write_back: Whether the item should write itself back to disk.
    :param traverse_children: Whether to traverse a directories children.

    """

    def __init__(
        self,
        path: pathlib.Path,
        write_back: bool = False,
        traverse_children: bool = False,
    ) -> None:
        super().__init__(path, write_back=write_back)

        self._traverse_children = traverse_children

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.path} traverse_children={self.traverse_children}>"

    # -------------------------------------------------------------------------
    # NON-PUBLIC METHODS
    # -------------------------------------------------------------------------

    def _get_child_items(self) -> List[BaseItem]:
        """Find child items to process.

        :return: A list of found child items.

        """
        items: List[BaseItem] = []

        for child in pathlib.Path(self.path).iterdir():
            # Skip hidden items.
            if not child.name[0].isalpha():
                continue

            if child.is_dir():
                # If there is an __init__.py file then we can treat the directory as a
                # Python package.
                if (child / "__init__.py").exists():
                    items.append(
                        PythonPackageDirectoryItem(child, write_back=self.write_back)
                    )

                # Otherwise, it's just another directory.
                else:
                    items.append(
                        DirectoryToProcess(
                            child, write_back=self.write_back, traverse_children=True
                        )
                    )

            else:
                # If the file is a Python file we can process it.
                if is_python_file(child):
                    items.append(FileToProcess(child, write_back=self.write_back))

        # If this is a test item then make any found child items also test items.
        if self.is_test_item:
            for item in items:
                item.is_test_item = True

        return items

    def _process_children(
        self, runner: houdini_package_runner.runners.base.HoudiniPackageRunner
    ) -> int:
        """Process an item.

        :param runner: The package runner processing the item.
        :return: The process return code.

        """
        items = self._get_child_items()

        result = 0

        # Process each item with the runner.
        for item in items:
            result |= item.process(runner)

        return result

    # -------------------------------------------------------------------------
    # PROPERTIES
    # -------------------------------------------------------------------------

    @property
    def traverse_children(self) -> bool:
        """Whether to traverse children."""
        return self._traverse_children

    # -------------------------------------------------------------------------
    # METHODS
    # -------------------------------------------------------------------------

    def process(
        self, runner: houdini_package_runner.runners.base.HoudiniPackageRunner
    ) -> int:
        """Process an item.

        :param runner: The package runner processing the item.
        :return: The process return code.

        """
        # If traversing children then we want to process them.
        if self.traverse_children:
            return self._process_children(runner)

        # Otherwise, process this directory.
        return runner.process_path(self.path, self)


class FileToProcess(BaseFileItem):
    """Class representing a file to process.

    :param path: The file path to process.
    :param write_back: Whether the item should write itself back to disk.
    :param display_name: Optional display name for test output.

    """

    def __init__(
        self, path: pathlib.Path, write_back: bool = False, display_name: str = None
    ) -> None:
        super().__init__(path, write_back=write_back)

        self._display_name = display_name

    def __repr__(self):
        path = self.display_name if self.display_name is not None else self.path

        return f"<{self.__class__.__name__} {path}>"

    # -------------------------------------------------------------------------
    # PROPERTIES
    # -------------------------------------------------------------------------

    @property
    def display_name(self) -> Optional[str]:
        """Display name for test output."""
        return self._display_name

    @display_name.setter
    def display_name(self, display_name: str):
        self._display_name = display_name

    # -------------------------------------------------------------------------
    # METHODS
    # -------------------------------------------------------------------------

    def process(
        self, runner: houdini_package_runner.runners.base.HoudiniPackageRunner
    ) -> int:
        """Process the file.

        :param runner: The package runner processing the item.
        :return: The process return code.

        """
        pre_hash = compute_file_hash(self.path)
        result = runner.process_path(self.path, self)
        post_hash = compute_file_hash(self.path)
        self.contents_changed = pre_hash != post_hash

        return result


class HoudiniDirectoryItem(DirectoryToProcess):
    """Subclass to represent a directory under a package houdini/ directory."""


class HoudiniScriptsDirectoryItem(DirectoryToProcess):
    """Subclass to represent a scripts/ directory under a package houdini directory."""

    def _get_child_items(self) -> List[BaseItem]:
        """Find child items to process.

        :return: A list of found child items.

        """
        items = super()._get_child_items()

        for item in items:
            # Mark any child files is ignoring the 'kwargs' builtin as it will always
            # exist in the handler scripts.
            if isinstance(item, FileToProcess):
                item.ignored_builtins.append("kwargs")

        return items


class PythonPackageDirectoryItem(DirectoryToProcess):
    """Subclass to represent a directory which is a Python package."""

    def __init__(self, path: pathlib.Path, write_back: bool = False) -> None:
        super().__init__(path, write_back=write_back)

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.path}>"


# =============================================================================
# FUNCTIONS
# =============================================================================


def compute_file_hash(file_path: pathlib.Path) -> str:
    """Compute a hash for the file contents.

    :param file_path: The path to the file to hash.
    :return: The computed file hash.

    """
    with open(file_path, "rb") as handle:
        file_hash = hashlib.md5()
        # TODO: Replace with walrus operator once we commit to Python 3.8+.
        # while chunk := handle.read(8192):
        chunk = handle.read(8192)
        while chunk:
            file_hash.update(chunk)
            chunk = handle.read(8192)

    return file_hash.hexdigest()


def is_python_file(
    file_path: pathlib.Path, python_bins: Optional[List[str]] = None
) -> bool:
    """Check if a file is a Python file.

    This function will do it's best to determine Whether a file is a Python file.

    It will:
      - Check if the extension is .py
      - Check if the first line is a #! line and Whether any of the python_bin names are in the line.

    :param file_path: The path to check.
    :param python_bins: Optional list of python executable names.
    :return: Whether this is a Python file.

    """
    ext = file_path.suffix

    if ext == ".py":
        return True

    if ext == ".pyc":
        return False

    # Try to peak at the first line.
    with file_path.open() as handle:
        try:
            first_line = handle.readline()

        except UnicodeDecodeError:
            return False

    python_bins = ["python"] if python_bins is None else python_bins

    # If the file is a script check if any of the python bin names are in the command.
    if first_line.startswith("#!"):
        for python_bin in python_bins:
            if python_bin in first_line:
                return True

    return False
