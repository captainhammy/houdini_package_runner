"""This module contains runnable items based on Houdini digital assets."""

# =============================================================================
# IMPORTS
# =============================================================================

# Future
from __future__ import annotations

# Standard Library
import json
import pathlib
import subprocess
from typing import TYPE_CHECKING, List

# Houdini Package Runner
from houdini_package_runner.items.base import BaseFileItem
from houdini_package_runner.items.dialog_script import DialogScriptItem
from houdini_package_runner.items.filesystem import FileToProcess
from houdini_package_runner.items.xml import ShelfFile

# Imports for type checking.
if TYPE_CHECKING:
    import houdini_package_runner.runners.base


# =============================================================================
# CLASSES
# =============================================================================


class ExpandedOperatorType(BaseFileItem):
    """Class representing an operator type inside an expanded digital asset
    folder.

    :param path: The path to the operator specific folder.
    :param name: The name of the operator.
    :param write_back: Whether the item should write itself back to disk.
    :param source_file: Optional source file for the expanded operator definition.

    """

    def __init__(
        self, path: pathlib.Path, name: str, write_back: bool = False, source_file: pathlib.PurePath = None
    ) -> None:
        super().__init__(path, write_back=write_back)

        self._name = name
        self._source_file = source_file

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.name} ({self.path})>"

    # -------------------------------------------------------------------------
    # NON-PUBLIC METHODS
    # -------------------------------------------------------------------------

    def _find_python_sections(self):
        """Build a list of all Python related section files to process.

        This list will include any section files with IsPython in ExtraFileOptions
        and the PythonCook section if it exists.

        """
        python_sections = []

        # The extra file options file.
        extra_options = self.path / "ExtraFileOptions"

        if extra_options.exists():
            with extra_options.open() as handle:
                data = json.load(handle)

            for key, values in data.items():
                # Look for sections that are Python.
                if "IsPython" in key:
                    if values["value"]:
                        script_name = key.split("/")[0]
                        section_path = self.path / script_name
                        python_sections.append(section_path)

        # PythonCook sections are implicitly Python so check for them manually.
        python_cook_path = self.path / "PythonCook"

        if python_cook_path.exists():
            python_sections.append(python_cook_path)

        files_to_process = []

        for section_path in python_sections:
            if self._source_file is not None:
                display_name = self._source_file / section_path.name

            else:
                display_name = self.path / section_path.name

            files_to_process.append(
                FileToProcess(section_path, write_back=self.write_back, display_name=display_name)
            )

        return files_to_process

    def _gather_items(self) -> List[BaseFileItem]:
        """Gather all operator related items.

        This includes any Python sections, shelf tools or Python code from the DialogScript.

        """
        items_to_process: List[BaseFileItem] = self._find_python_sections()

        shelf_path = self.path / "Tools.shelf"

        if shelf_path.exists():
            display_name = None

            if self._source_file is not None:
                display_name = str(self._source_file / "Tools.shelf")

            items_to_process.append(
                ShelfFile(shelf_path, write_back=self.write_back, display_name=display_name, tool_name=self.name)
            )

        dialog_script_path = self.path / "DialogScript"

        if self._source_file is not None:
            display_name = self._source_file.stem.replace("::", "__") + "_DialogScript"

        else:
            display_name = (
                self.name.replace("::", "__").replace("/", "_") + "_DialogScript"
            )

        items_to_process.append(DialogScriptItem(dialog_script_path, display_name, write_back=self.write_back))

        return items_to_process

    # -------------------------------------------------------------------------
    # PROPERTIES
    # -------------------------------------------------------------------------

    @property
    def name(self) -> str:
        """The name of the operator."""
        return self._name

    # -------------------------------------------------------------------------
    # METHODS
    # -------------------------------------------------------------------------

    def process(
        self, runner: houdini_package_runner.runners.base.HoudiniPackageRunner
    ) -> bool:
        """Process the operator items.

        :param runner: The package runner processing the item.
        :return: Whether processing was successful.

        """
        items_to_process = self._gather_items()

        success = True

        for item in items_to_process:
            success &= item.process(runner)
            self.contents_changed |= item.contents_changed

        return success


class DigitalAssetDirectory(BaseFileItem):
    """Class representing an extracted otl file."""

    def __init__(
        self, path: pathlib.Path, write_back=False, source_file: pathlib.PurePath = None
    ) -> None:
        super().__init__(path, write_back=write_back)

        self._source_file = source_file

    # -------------------------------------------------------------------------
    # NON-PUBLIC METHODS
    # -------------------------------------------------------------------------

    def _build_operator_list(self) -> List[ExpandedOperatorType]:
        """Build a list of operators in the extracted library.

        :return: A list of operators inside the library.

        """
        operators = []

        sections_list = self.path / "Sections.list"

        if not sections_list.exists():
            raise RuntimeError(
                f"Could not find Sections.list in extracted otl folder: {self.path}"
            )

        with sections_list.open() as handle:
            data = handle.readlines()

        results = []

        for line in data:
            components = line.split()

            if components:
                if (self.path / components[0]).is_dir():
                    results.append(components)

        for definition in results:
            display_name = None

            if self._source_file is not None:
                display_name = pathlib.PurePath(f"{self._source_file}?{definition[1]}")

            operator = ExpandedOperatorType(
                self.path / definition[0], definition[1], write_back=self.write_back, source_file=display_name
            )

            operators.append(operator)

        return operators

    # -------------------------------------------------------------------------
    # METHODS
    # -------------------------------------------------------------------------

    def process(
        self, runner: houdini_package_runner.runners.base.HoudiniPackageRunner
    ) -> bool:
        """Process the file.

        :param runner: The package runner processing the item.
        :return: Whether processing was successful..

        """
        operators = self._build_operator_list()

        success = True

        for operator in operators:
            success &= operator.process(runner)
            self.contents_changed |= operator.contents_changed

        return success


class BinaryDigitalAssetFile(BaseFileItem):
    """Class representing a binary digital asset file that will be extracted for testing."""

    # -------------------------------------------------------------------------
    # METHODS
    # -------------------------------------------------------------------------

    def process(
        self, runner: houdini_package_runner.runners.base.HoudiniPackageRunner
    ) -> bool:
        """Process the binary digital asset file.

        :param runner: The package runner processing the item.
        :return: Whether processing was successful.

        """
        file_name = self.path.name

        target_folder = runner.temp_dir / file_name

        subprocess.call(
            [runner.hotl_command, "-t", target_folder, self.path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Create a new DigitalAssetDirectory and process it.
        asset_directory = DigitalAssetDirectory(target_folder, write_back=self.write_back, source_file=self.path)

        result = asset_directory.process(runner)

        self.contents_changed = asset_directory.contents_changed

        # If writing back, call 'hotl -l' to collapse all the changes.
        if self.write_back and self.contents_changed:
            subprocess.call(
                [runner.hotl_command, "-l", target_folder, self.path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        return result


# =============================================================================
# FUNCTIONS
# =============================================================================


def is_expanded_digital_asset_dir(path: pathlib.Path) -> bool:
    """Check if a folder is an expanded digital asset.

    We say a folder is an expanded digital asset if it has a "Sections.list" file inside.

    :param path: The folder to check.
    :return: Whether the folder is an expanded digital asset.

    """
    return (path / "Sections.list").is_file()
