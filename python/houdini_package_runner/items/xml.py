"""This module contains runnable items related to Houdini XML definitions."""

# =============================================================================
# IMPORTS
# =============================================================================

# Future
from __future__ import annotations

# Standard Library
import abc
from typing import TYPE_CHECKING, List, Tuple

# Third Party
from lxml import etree

# Houdini Package Runner
from houdini_package_runner.items.filesystem import FileToProcess

# Imports for type checking.
if TYPE_CHECKING:
    import pathlib

    from houdini_package_runner.runners.base import HoudiniPackageRunner

    ItemsToProcess = List[
        Tuple[etree._Element, str]  # pylint: disable=protected-access
    ]


# =============================================================================
# CLASSES
# =============================================================================


class XMLBase(FileToProcess, metaclass=abc.ABCMeta):
    """The base class for XML based Houdini files."""

    # -------------------------------------------------------------------------
    # NON-PUBLIC METHODS
    # -------------------------------------------------------------------------

    def _process_code_section(
        self,
        section: etree._Element,  # pylint: disable=protected-access
        runner: HoudiniPackageRunner,
        base_file_name: str,
    ) -> bool:
        """Process an XML section's text.

        :param section: The section to process.
        :param runner: The package runner processing the item.
        :param base_file_name: The name of the temporary file.
        :return: Whether processing was successful.

        """
        # Check if the code blob is in a CDATA block.
        has_cdata = "CDATA" in etree.tostring(section, encoding="unicode")

        # Get the text of the section.
        script_code = section.text

        # Create a temp Python file for the code blob.
        temp_path = runner.temp_dir / f"{base_file_name}.py"

        # Dump the code to the temp file, so it can be processed.
        with temp_path.open("w") as handle:
            handle.write(str(script_code))
            handle.flush()

        result = runner.process_path(temp_path, self)

        if self.write_back:
            # Read the possibly modified file.
            with temp_path.open("r") as handle:
                contents = handle.read()

            # If the original code was in a CDATA block, wrap the result in one and set it
            # back to the section.
            if has_cdata:
                section.text = etree.CDATA(contents)

            # Otherwise, just use the raw values.
            else:
                section.text = contents

            if section.text != script_code:
                self.contents_changed = True

        return result

    @abc.abstractmethod
    def _get_items_to_process(
        self,
        root: etree._Element,  # pylint: disable=protected-access
    ) -> ItemsToProcess:
        """Get any xml items that need to be processed.

        :param root: An xml element.
        :return: A list of items to be processed.

        """

    # -------------------------------------------------------------------------
    # METHODS
    # -------------------------------------------------------------------------

    def process(self, runner: HoudiniPackageRunner) -> bool:
        """Process the file.

        :param runner: The package runner processing the item.
        :return: Whether processing was successful.

        """
        parser = etree.XMLParser(strip_cdata=False)
        tree = etree.parse(str(self.path), parser)

        root = tree.getroot()

        items_to_process = self._get_items_to_process(root)

        success = True

        for item in items_to_process:
            success &= self._process_code_section(item[0], runner, item[1])

        if self.write_back and self.contents_changed:
            tree.write(str(self.path), encoding="utf-8", xml_declaration=True)

        return success


class MenuFile(XMLBase):
    """An xml menu file."""

    # -------------------------------------------------------------------------
    # NON-PUBLIC METHODS
    # -------------------------------------------------------------------------

    def _get_items_to_process(
        self,
        root: etree._Element,  # pylint: disable=protected-access
    ) -> ItemsToProcess:
        """Get any xml items that need to be processed.

        For XML menu files we look for 'scriptItem' entries and attempt to
        grab their 'scriptCode' and 'context/expression' contents.

        :param root: An xml element.
        :return: A list of items to be processed.

        """
        items = []

        for script_item in root.iter(tag="scriptItem"):
            code = script_item.find("scriptCode")

            if code is not None:
                items.append((code, str(script_item.attrib["id"])))

                context = script_item.find("context/expression")

                if context is not None:
                    items.append((context, f"{script_item.get('id'):s}.context"))

        return items


class PythonPanelFile(XMLBase):
    """A python panel file."""

    # -------------------------------------------------------------------------
    # NON-PUBLIC METHODS
    # -------------------------------------------------------------------------

    def _get_items_to_process(
        self,
        root: etree._Element,  # pylint: disable=protected-access
    ) -> ItemsToProcess:
        """Get any xml items that need to be processed.

        :param root: An xml element.
        :return: A list of items to be processed.

        """
        items = []

        for interface in root:
            script = interface.find("script")

            if script is None:
                continue

            items.append((script, str(interface.attrib["name"])))

        return items


class ShelfFile(XMLBase):
    """A shelf file.

    :param path: The shelf file path.
    :param display_name: Optional display name.
    :param tool_name: Optional tool name.

    """

    def __init__(
        self,
        path: pathlib.Path,
        write_back: bool = False,
        display_name: str = None,
        tool_name: str = None,
    ) -> None:
        super().__init__(path, write_back, display_name)

        self._tool_name = tool_name

    # -------------------------------------------------------------------------
    # NON-PUBLIC METHODS
    # -------------------------------------------------------------------------

    def _get_items_to_process(
        self,
        root: etree._Element,  # pylint: disable=protected-access
    ) -> ItemsToProcess:
        """Get any xml items that need to be processed.

        :param root: An xml element.
        :return: A list of items to be processed.

        """
        items = []

        for tool in root:
            script = tool.find("script")

            if script is None:
                continue

            language = script.get("scriptType")

            if language != "python":
                continue

            tool_name = str(tool.attrib["name"])

            if self._tool_name is not None and tool_name == "$HDA_DEFAULT_TOOL":
                tool_name = (
                    self._tool_name.replace("::", "__").replace("/", "_")
                    + "_DEFAULT_TOOL"
                )

            items.append((script, tool_name))

        return items
