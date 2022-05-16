"""Test the houdini_package_runner.discoverers.package module."""

# =============================================================================
# IMPORTS
# =============================================================================

# Standard Library
import argparse
import pathlib

# Third Party
import pytest

# Houdini Package Runner
import houdini_package_runner.discoverers.base
import houdini_package_runner.discoverers.package
import houdini_package_runner.items.digital_asset
import houdini_package_runner.items.filesystem
import houdini_package_runner.items.xml

# =============================================================================
# TESTS
# =============================================================================


class TestPackageItemDiscoverer:
    """Test houdini_package_runner.discoverers.package.PackageItemDiscoverer."""

    # Object construction

    @pytest.mark.parametrize("has_items", (False, True))
    def test___init__(self, mocker, has_items):
        """Test object initialization."""
        mock_path = mocker.MagicMock(spec=pathlib.Path)

        mock_file_path = mocker.MagicMock(spec=pathlib.Path)
        mock_file_path.is_file.return_value = True
        mock_file_path.is_dir.return_value = False

        mock_file1 = mocker.MagicMock(
            spec=houdini_package_runner.items.filesystem.FileToProcess
        )
        mock_dir = mocker.MagicMock(
            spec=houdini_package_runner.items.filesystem.DirectoryToProcess
        )

        mock_process_dir = mocker.patch(
            "houdini_package_runner.discoverers.package.process_directory"
        )
        mock_process_dir.side_effect = (mock_dir, None)

        mock_houdini_item = mocker.MagicMock(
            spec=houdini_package_runner.items.filesystem.HoudiniDirectoryItem
        )

        mock_get_houdini = mocker.patch(
            "houdini_package_runner.discoverers.package.get_houdini_items"
        )
        mock_get_houdini.return_value = [mock_houdini_item] if has_items else []

        mock_file_to_process = mocker.patch(
            "houdini_package_runner.items.filesystem.FileToProcess"
        )

        if has_items:
            items = [mock_file1]

            houdini_items = ["scripts"]

            mock_dir1 = mocker.MagicMock(spec=pathlib.Path)
            mock_dir1.is_file.return_value = False
            mock_dir1.is_dir.return_value = True

            mock_dir2 = mocker.MagicMock(spec=pathlib.Path)
            mock_dir2.is_file.return_value = False
            mock_dir2.is_dir.return_value = True

            extra_paths = [mock_file_path, mock_dir1, mock_dir2]

            inst = houdini_package_runner.discoverers.package.PackageItemDiscoverer(
                mock_path,
                houdini_items,
                extra_paths=extra_paths,
                items=items,
            )

            assert inst.items == [
                mock_file1,
                mock_houdini_item,
                mock_file_to_process.return_value,
                mock_dir,
            ]

            mock_file_to_process.assert_called_with(mock_file_path)
            mock_get_houdini.assert_called_with(houdini_items, inst.path)

        else:
            inst = houdini_package_runner.discoverers.package.PackageItemDiscoverer(
                mock_path,
                houdini_items=[],
            )

            assert inst.items == []


def test_get_digital_asset_items(shared_datadir):
    """Test houdini_package_runner.discoverers.package.get_digital_asset_items."""
    test_path = shared_datadir / "get_digital_asset_items"

    results = houdini_package_runner.discoverers.package.get_digital_asset_items(
        test_path
    )

    assert len(results) == 3

    expanded_dir_path = test_path / "expanded_dir"
    nodetype_otl_path = test_path / "nodetype.otl"
    operator_hda_path = test_path / "operator.hda"

    for item in results:
        if item.path in (nodetype_otl_path, operator_hda_path):
            assert isinstance(
                item, houdini_package_runner.items.digital_asset.BinaryDigitalAssetFile
            )

        elif item.path == expanded_dir_path:
            assert isinstance(
                item, houdini_package_runner.items.digital_asset.DigitalAssetDirectory
            )


def test_get_houdini_items(mocker, shared_datadir):
    """Test houdini_package_runner.discoverers.package.get_houdini_items."""
    mock_asset_item = mocker.MagicMock(
        spec=houdini_package_runner.items.digital_asset.BinaryDigitalAssetFile
    )
    mock_get_asset_items = mocker.patch(
        "houdini_package_runner.discoverers.package.get_digital_asset_items",
        return_value=[mock_asset_item],
    )

    mock_tool_item = mocker.MagicMock(spec=houdini_package_runner.items.xml.ShelfFile)
    mock_get_tool_items = mocker.patch(
        "houdini_package_runner.discoverers.package.get_tool_items",
        return_value=[mock_tool_item],
    )

    mock_panel_item = mocker.MagicMock(
        spec=houdini_package_runner.items.xml.PythonPanelFile
    )
    mock_get_panel_items = mocker.patch(
        "houdini_package_runner.discoverers.package.get_python_panel_items",
        return_value=[mock_panel_item],
    )

    mock_menu_item = mocker.MagicMock(spec=houdini_package_runner.items.xml.MenuFile)
    mock_get_menu_items = mocker.patch(
        "houdini_package_runner.discoverers.package.get_menu_items",
        return_value=[mock_menu_item],
    )

    mock_pydir_item = mocker.patch(
        "houdini_package_runner.items.filesystem.HoudiniDirectoryItem"
    )

    mock_dir_item = mocker.MagicMock(
        spec=houdini_package_runner.items.filesystem.DirectoryToProcess
    )

    mock_process = mocker.patch(
        "houdini_package_runner.discoverers.package.process_directory",
        side_effect=(mock_dir_item, None),
    )

    test_path = shared_datadir / "get_houdini_items"

    item_names = [
        "",
        "otls",
        "hda",
        "directory_item",
        "empty_directory_item",
        "pythonXlibs",
        "toolbar",
        "python_panels",
        "menus",
        "some_file",
    ]

    items = houdini_package_runner.discoverers.package.get_houdini_items(
        item_names, test_path
    )

    expected = [
        mock_asset_item,
        mock_dir_item,
        mock_pydir_item.return_value,
        mock_tool_item,
        mock_panel_item,
        mock_menu_item,
    ]

    assert items == expected

    mock_get_asset_items.assert_called_with(test_path / "otls")
    mock_get_tool_items.assert_called_with(test_path / "toolbar")
    mock_get_panel_items.assert_called_with(test_path / "python_panels")
    mock_get_menu_items.assert_called_with(test_path)

    mock_pydir_item.assert_called_with(
        test_path / "python3.7libs", traverse_children=True
    )

    mock_process.assert_has_calls(
        [
            mocker.call(test_path / "directory_item"),
            mocker.call(test_path / "empty_directory_item"),
        ]
    )


def test_get_menu_items(mocker):
    """Test houdini_package_runner.discoverers.package.get_menu_items."""
    mock_menu_file = mocker.patch("houdini_package_runner.items.xml.MenuFile")

    mock_menu_path = mocker.MagicMock(spec=pathlib.Path)

    mock_houdini_root = mocker.MagicMock(spec=pathlib.Path)
    mock_houdini_root.glob.return_value = [mock_menu_path]

    result = houdini_package_runner.discoverers.package.get_menu_items(
        mock_houdini_root
    )

    assert result == [mock_menu_file.return_value]

    mock_houdini_root.glob.assert_called_with("*.xml")
    mock_menu_file.assert_called_with(mock_menu_path)


def test_get_python_panel_items(mocker):
    """Test houdini_package_runner.discoverers.package.get_python_panel_items."""
    mock_panel_file = mocker.patch("houdini_package_runner.items.xml.PythonPanelFile")

    mock_panel_path = mocker.MagicMock(spec=pathlib.Path)

    mock_panel_root = mocker.MagicMock(spec=pathlib.Path)
    mock_panel_root.glob.return_value = [mock_panel_path]

    result = houdini_package_runner.discoverers.package.get_python_panel_items(
        mock_panel_root
    )

    assert result == [mock_panel_file.return_value]

    mock_panel_root.glob.assert_called_with("*.pypanel")
    mock_panel_file.assert_called_with(mock_panel_path)


def test_get_tool_items(mocker):
    """Test houdini_package_runner.discoverers.package.get_tool_items."""
    mock_shelf_file = mocker.patch("houdini_package_runner.items.xml.ShelfFile")

    mock_shelf_path = mocker.MagicMock(spec=pathlib.Path)

    mock_toolbar_path = mocker.MagicMock(spec=pathlib.Path)
    mock_toolbar_path.glob.return_value = [mock_shelf_path]

    result = houdini_package_runner.discoverers.package.get_tool_items(
        mock_toolbar_path
    )

    assert result == [mock_shelf_file.return_value]

    mock_toolbar_path.glob.assert_called_with("*.shelf")
    mock_shelf_file.assert_called_with(mock_shelf_path)


def test_init_standard_package_discoverer(
    mocker,
):
    """Test houdini_package_runner.discoverers.package.init_standard_package_discoverer."""
    mock_discoverer = mocker.patch(
        "houdini_package_runner.discoverers.package.PackageItemDiscoverer"
    )

    mock_root = mocker.MagicMock(spec=pathlib.Path)
    mock_houdini_root = mocker.MagicMock(spec=pathlib.Path)
    mock_extra_paths = mocker.MagicMock(spec=list)
    mock_houdini_items = mocker.MagicMock(spec=list)

    mock_parse = mocker.patch(
        "houdini_package_runner.parser.process_common_arg_settings"
    )
    mock_parse.return_value = (
        mock_root,
        mock_houdini_root,
        mock_extra_paths,
        mock_houdini_items,
    )

    mock_namespace = mocker.MagicMock(spec=argparse.Namespace)

    result = (
        houdini_package_runner.discoverers.package.init_standard_package_discoverer(
            mock_namespace
        )
    )

    assert result == mock_discoverer.return_value

    mock_parse.assert_called_with(mock_namespace)

    mock_discoverer.assert_called_with(
        mock_houdini_root,
        houdini_items=mock_houdini_items,
        extra_paths=mock_extra_paths,
    )


@pytest.mark.parametrize(
    "test_path, expected",
    (
        (
            "package_dir",
            houdini_package_runner.items.filesystem.PythonPackageDirectoryItem,
        ),
        ("python", houdini_package_runner.items.filesystem.PythonPackageDirectoryItem),
        (
            "scripts",
            houdini_package_runner.items.filesystem.HoudiniScriptsDirectoryItem,
        ),
        ("tests", houdini_package_runner.items.filesystem.DirectoryToProcess),
        ("other", houdini_package_runner.items.filesystem.DirectoryToProcess),
    ),
)
def test_process_directory(shared_datadir, test_path, expected):
    """Test houdini_package_runner.discoverers.package.process_directory."""
    test_dir = shared_datadir / "process_directory" / test_path

    result = houdini_package_runner.discoverers.package.process_directory(test_dir)

    assert isinstance(result, expected)

    # Items which aren't Python packages should have 'traverse_children' set.
    if not isinstance(
        result, houdini_package_runner.items.filesystem.PythonPackageDirectoryItem
    ):
        assert result.traverse_children

    if test_path == "tests":
        assert result.is_test_item
