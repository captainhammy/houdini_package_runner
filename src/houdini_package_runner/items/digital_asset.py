"""This module contains runnable items based on Houdini digital assets."""

# =============================================================================
# IMPORTS
# =============================================================================

# Future
from __future__ import annotations

# Standard Library
import json
import os
import pathlib
from typing import TYPE_CHECKING, List, Optional

# Houdini Package Runner
import houdini_package_runner.utils
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


class DigitalAssetPythonSection(FileToProcess):
    """Class representing a Python digital asset section to process.

    :param path: The file path to process.
    :param display_name: Display name for test output.
    :param write_back: Whether the item should write itself back to disk.

    """

    def __init__(
        self, path: pathlib.Path, display_name: str, write_back: bool = False
    ) -> None:
        super().__init__(path, write_back=write_back, display_name=display_name)

        section_name = os.path.basename(display_name)

        if section_name not in ("PythonCook", "PythonModule"):
            self.ignored_builtins.append("kwargs")


class ExpandedOperatorType(BaseFileItem):
    """Class representing an operator type inside an expanded digital asset
    folder.

    :param path: The path to the operator specific folder.
    :param name: The name of the operator.
    :param write_back: Whether the item should write itself back to disk.
    :param source_file: Optional source file for the expanded operator definition.

    """

    def __init__(
        self,
        path: pathlib.Path,
        name: str,
        write_back: bool = False,
        source_file: pathlib.PurePath = None,
    ) -> None:
        super().__init__(path, write_back=write_back)

        self._name = name
        self._source_file = source_file

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.name} ({self.path})>"

    # -------------------------------------------------------------------------
    # NON-PUBLIC METHODS
    # -------------------------------------------------------------------------

    def _build_python_section_items(
        self, python_sections: List[pathlib.Path]
    ) -> List[FileToProcess]:
        """Build a list of files to process based on Python sections.

        :param python_sections: The Python section files to process.
        :return: The created Python section items.

        """
        files_to_process = []

        for section_path in python_sections:
            if self._source_file is not None:
                display_name = self._source_file / section_path.name

            else:
                display_name = self.path / section_path.name

            files_to_process.append(
                DigitalAssetPythonSection(
                    section_path,
                    str(display_name),
                    write_back=self.write_back,
                )
            )

        return list(files_to_process)

    def _find_internal_shelf_item(self) -> Optional[ShelfFile]:
        """Find the internal shelf item to process, if possible.

        :return: An item representing the internal tool shelves, if any.

        """

        shelf_path = self.path / "Tools.shelf"

        if not shelf_path.exists():
            return None

        display_name = None

        if self._source_file is not None:
            display_name = str(self._source_file / "Tools.shelf")

        item = ShelfFile(
            shelf_path,
            write_back=self.write_back,
            display_name=display_name,
            tool_name=self.name,
        )

        return item

    def _find_python_section_paths(self) -> List[pathlib.Path]:
        """Build a list of all Python related section files to process.

        This list will include any section files with IsPython in ExtraFileOptions
        and the PythonCook section if it exists.

        :return: A list of Python file sections.

        """
        python_sections = self._get_extra_python_section_files()

        # PythonCook sections are implicitly Python so check for them manually.
        python_cook_path = self.path / "PythonCook"

        if python_cook_path.exists():
            python_sections.append(python_cook_path)

        return python_sections

    def _gather_items(self) -> List[BaseFileItem]:
        """Gather all operator related items.

        This includes any Python sections, shelf tools or Python code from the DialogScript.

        :return: A list of all the processable items associated with the expanded digital asset.

        """
        python_sections = self._find_python_section_paths()

        items_to_process: List[BaseFileItem] = list(
            self._build_python_section_items(python_sections)
        )

        shelf_item = self._find_internal_shelf_item()

        if shelf_item is not None:
            items_to_process.append(shelf_item)

        items_to_process.append(self._get_dialog_script_item())

        return items_to_process

    def _get_dialog_script_item(self) -> DialogScriptItem:
        """Get an item for processing the DialogScript section.

        :return: The DialogScript item.

        """
        dialog_script_path = self.path / "DialogScript"

        if self._source_file is not None:
            display_name = self._source_file.stem.replace("::", "__") + "_DialogScript"

        else:
            display_name = (
                self.name.replace("::", "__").replace("/", "_") + "_DialogScript"
            )

        return DialogScriptItem(
            dialog_script_path, display_name, write_back=self.write_back
        )

    def _get_extra_python_section_files(self) -> List[pathlib.Path]:
        """Find any sections which contain Python code.

        :return: Any section files which contain Python code.

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

        return python_sections

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
    ) -> int:
        """Process the operator items.

        :param runner: The package runner processing the item.
        :return: The process return code.

        """
        items_to_process = self._gather_items()

        result = 0

        for item in items_to_process:
            result |= item.process(runner)
            self.contents_changed |= item.contents_changed

        return result


class DigitalAssetDirectory(BaseFileItem):
    """Class representing an extracted otl file.

    :param path: The path for the item.
    :param write_back: Whether the item should write itself back to disk.
    :param source_file: The binary source file, if any.

    """

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

        operator_dirs = self._find_operator_dirs()

        for definition in operator_dirs:
            directory_name, operator_name = definition
            display_name = None

            if self._source_file is not None:
                display_name = pathlib.PurePath(f"{self._source_file}?{operator_name}")

            operator = ExpandedOperatorType(
                self.path / directory_name,
                operator_name,
                write_back=self.write_back,
                source_file=display_name,
            )

            operators.append(operator)

        return operators

    def _find_operator_dirs(self) -> List[List[str]]:
        """Find a list of operator definition directories based on the Sections.list.

        :return: A list of any directories containing operator definitions.

        """
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

            if len(components) == 2:
                if (self.path / components[0]).is_dir():
                    results.append(components)

        return results

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
        operators = self._build_operator_list()

        result = 0

        for operator in operators:
            result |= operator.process(runner)
            self.contents_changed |= operator.contents_changed

        return result


class BinaryDigitalAssetFile(BaseFileItem):
    """Class representing a binary digital asset file that will be extracted for testing."""

    # -------------------------------------------------------------------------
    # NON-PUBLIC METHODS
    # -------------------------------------------------------------------------

    def _collapse_dir(self, hotl_command: str, target_folder: pathlib.Path) -> None:
        """Collapse the target folder to the digital asset file.

        :param hotl_command: The hotl command to use.
        :param target_folder: The folder to collapse.

        """
        command = [hotl_command, "-l", str(target_folder), str(self.path)]

        return_code = houdini_package_runner.utils.execute_subprocess_command(command)

        if return_code:
            raise RuntimeError(f"An error occurred running the command: {command}")

    def _extract_file(self, hotl_command: str, target_folder: pathlib.Path) -> None:
        """Expand the digital asset file to the target folder.

        :param hotl_command: The hotl command to use.
        :param target_folder: The folder to expand to.

        """
        command = [hotl_command, "-t", str(target_folder), str(self.path)]

        return_code = houdini_package_runner.utils.execute_subprocess_command(command)

        if return_code:
            raise RuntimeError(f"An error occurred running the command: {command}")

    # -------------------------------------------------------------------------
    # METHODS
    # -------------------------------------------------------------------------

    def process(
        self, runner: houdini_package_runner.runners.base.HoudiniPackageRunner
    ) -> int:
        """Process the binary digital asset file.

        :param runner: The package runner processing the item.
        :return: The process return code.

        """
        target_folder = runner.temp_dir / self.path.name

        self._extract_file(runner.hotl_command, target_folder)

        # Create a new DigitalAssetDirectory and process it.
        asset_directory = DigitalAssetDirectory(
            target_folder, write_back=self.write_back, source_file=self.path
        )

        result = asset_directory.process(runner)

        self.contents_changed = asset_directory.contents_changed

        # If writing back, call 'hotl -l' to collapse all the changes.
        if self.write_back and self.contents_changed:
            self._collapse_dir(runner.hotl_command, target_folder)

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
