"""This module contains a class to discover package items."""

# =============================================================================
# IMPORTS
# =============================================================================

# Future
from __future__ import annotations

# Standard Library
import pathlib
from typing import TYPE_CHECKING, List, Optional

# Houdini Package Runner
import houdini_package_runner.parser
from houdini_package_runner.discoverers.base import BaseItemDiscoverer
from houdini_package_runner.items import digital_asset, filesystem, xml

# Imports for type checking.
if TYPE_CHECKING:
    import argparse

    from houdini_package_runner.items.base import BaseItem


# =============================================================================
# CLASSES
# =============================================================================


class PackageItemDiscoverer(BaseItemDiscoverer):
    """This class is responsible for searching for various items to process.

    :param path: The path to start searching for items from.
    :param houdini_items: A list of Houdini related directories to look for.
    :param files: A list of extra files to search for.
    :param directories: A list of extra directories to search for.
    :param items: Optional list of specific items to check.

    """

    def __init__(
        self,
        path: pathlib.Path,
        houdini_items: Optional[List[str]] = None,
        files: Optional[List[pathlib.Path]] = None,
        directories: Optional[List[pathlib.Path]] = None,
        items: Optional[List[BaseItem]] = None,
    ) -> None:
        super().__init__(path, items=items)

        if files:
            self.items.extend(
                [filesystem.FileToProcess(file_path) for file_path in files]
            )

        if directories:
            for dir_path in directories:
                result = process_directory(dir_path)

                if result is not None:
                    self.items.append(result)

        if houdini_items:
            self.items.extend(get_houdini_items(houdini_items, self.path / "houdini"))


# =============================================================================
# FUNCTIONS
# =============================================================================


def get_digital_asset_items(otl_path: pathlib.Path) -> List[BaseItem]:
    """Get a list of shelf items to process.

    :param otl_path: The path to the otls folder.
    :return: A list otl items.

    """
    items: List[BaseItem] = []

    for otl_folder in otl_path.iterdir():
        if otl_folder.is_dir() and digital_asset.is_expanded_digital_asset_dir(otl_folder):
            extracted_otl = digital_asset.DigitalAssetDirectory(otl_folder)
            items.append(extracted_otl)

        elif otl_folder.suffix in (".hda", ".otl"):

            otl_file = digital_asset.BinaryDigitalAssetFile(otl_folder)
            items.append(otl_file)

    return items


def get_houdini_items(houdini_items: List[str], houdini_root: pathlib.Path) -> List[BaseItem]:
    """Get Houdini-related items to process.

    :param houdini_items: The Houdini item names.
    :param houdini_root: The root houdini directory.
    :return: The Houdini items to process.

    """
    items = []

    for item_name in houdini_items:
        if not item_name:
            continue

        item_path = houdini_root / item_name

        if item_name in ("otls", "hda"):
            if not item_path.is_dir():
                continue

            items.extend(get_digital_asset_items(item_path))

        elif item_name == "toolbar":
            items.extend(get_tool_items(item_path))

        elif item_name == "python_panels":
            items.extend(get_python_panel_items(item_path))

        elif item_name == "menus":
            items.extend(get_menu_items(houdini_root))

        elif item_name in ("python2.7libs", "python3.7libs"):
            if item_path.exists():
                items.append(
                    filesystem.HoudiniDirectoryItem(
                        item_path, traverse_children=True
                    )
                )

        else:
            if not item_path.is_dir():
                continue

            item = process_directory(item_path)

            if item is not None:
                items.append(item)

    return items


def get_menu_items(houdini_root: pathlib.Path) -> List[xml.MenuFile]:
    """Get a list of shelf items to process.

    :param houdini_root: The path to the houdini folder.
    :return: A list of menu items.

    """
    menu_files = [xml.MenuFile(menu_file) for menu_file in houdini_root.glob("*.xml")]

    return menu_files


def get_python_panel_items(panel_dir: pathlib.Path) -> List[xml.PythonPanelFile]:
    """Get a list of shelf items to process.

    :param panel_dir: The path to the shelf file folder.
    :return: A list of shelf python panel items.

    """
    panel_files = [
        xml.PythonPanelFile(panel_file) for panel_file in panel_dir.glob("*.pypanel")
    ]

    return panel_files


def get_tool_items(toolbar_path: pathlib.Path) -> List[xml.ShelfFile]:
    """Get a list of shelf items to process.

    :param toolbar_path: The path to the shelf file folder.
    :return: A list of shelf tool items.

    """
    shelf_files = [
        xml.ShelfFile(shelf_file) for shelf_file in toolbar_path.glob("*.shelf")
    ]

    return shelf_files


def init_standard_discoverer(parsed_args: argparse.Namespace) -> PackageItemDiscoverer:
    """Create a standard PackageItemDiscoverer based on standard args.

    :param parsed_args: The parsed script args.
    :return: A discoverer object based on the parsed args.

    """
    (
        path,
        dirs,
        files,
        houdini_items,
    ) = houdini_package_runner.parser.process_common_arg_settings(parsed_args)

    discoverer = PackageItemDiscoverer(
        path,
        houdini_items=houdini_items,
        files=files,
        directories=dirs,
    )

    return discoverer


def process_directory(dir_path: pathlib.Path) -> filesystem.DirectoryToProcess:
    """Process a directory to determine its item type.

    :return: The corresponding directory item type.

    """
    if (dir_path / "__init__.py").exists():
        return filesystem.PythonPackageDirectoryItem(dir_path)

    if dir_path.name == "python":
        return filesystem.PythonPackageDirectoryItem(dir_path)

    if dir_path.name == "tests":
        item = filesystem.DirectoryToProcess(dir_path, traverse_children=True)
        item.is_test_item = True

        return item

    return filesystem.DirectoryToProcess(dir_path, traverse_children=True)
