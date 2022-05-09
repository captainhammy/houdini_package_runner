"""Test the houdini_package_runner.items.digital_asset module."""

# =============================================================================
# IMPORTS
# =============================================================================

# Standard Library
import pathlib

# Third Party
import pytest

# Houdini Package Runner
import houdini_package_runner.items.base
import houdini_package_runner.items.dialog_script
import houdini_package_runner.items.digital_asset
import houdini_package_runner.items.filesystem
import houdini_package_runner.items.xml
import houdini_package_runner.runners.base

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def init_expanded(mocker):
    """Initialize a dummy ExpandedOperatorType for testing."""
    mocker.patch.multiple(
        houdini_package_runner.items.digital_asset.ExpandedOperatorType,
        __init__=lambda x, y, z, u, v: None,
    )

    def _create():
        return houdini_package_runner.items.digital_asset.ExpandedOperatorType(
            None, None, None, None
        )

    return _create


@pytest.fixture
def init_asset_dir(mocker):
    """Initialize a dummy DigitalAssetDirectory for testing."""
    mocker.patch.multiple(
        houdini_package_runner.items.digital_asset.DigitalAssetDirectory,
        __init__=lambda x, y, z, u: None,
    )

    def _create():
        return houdini_package_runner.items.digital_asset.DigitalAssetDirectory(
            None, None, None
        )

    return _create


@pytest.fixture
def init_binary(mocker):
    """Initialize a dummy BinaryDigitalAssetFile for testing."""
    mocker.patch.multiple(
        houdini_package_runner.items.digital_asset.BinaryDigitalAssetFile,
        __init__=lambda x, y, z: None,
    )

    def _create():
        return houdini_package_runner.items.digital_asset.BinaryDigitalAssetFile(
            None, None
        )

    return _create


# =============================================================================
# TESTS
# =============================================================================


class TestDigitalAssetPythonSection:
    """Test houdini_package_runner.items.digital_asset.DigitalAssetPythonSection."""

    @pytest.mark.parametrize(
        "section_name, write_back",
        (
            ("OnCreated", False),
            ("PythonModule", True),
            ("PythonCook", True),
        ),
    )
    def test___init__(self, mocker, section_name, write_back):
        """Test object initialization."""
        mock_path = mocker.MagicMock(spec=pathlib.Path)
        name = "/some/path/" + section_name

        if write_back:
            inst = houdini_package_runner.items.digital_asset.DigitalAssetPythonSection(
                mock_path,
                name,
                write_back=write_back,
            )

        else:
            inst = houdini_package_runner.items.digital_asset.DigitalAssetPythonSection(
                mock_path, name
            )

        if section_name not in ("PythonCook", "PythonModule"):
            assert "kwargs" in inst.ignored_builtins


class TestExpandedOperatorType:
    """Test houdini_package_runner.items.digital_asset.ExpandedOperatorType."""

    @pytest.mark.parametrize("write_back", (False, True))
    def test___init__(self, mocker, write_back):
        """Test object initialization."""
        mock_path = mocker.MagicMock(spec=pathlib.Path)
        mock_name = mocker.MagicMock(spec=str)
        mock_source_file = mocker.MagicMock(spec=pathlib.PurePath)

        mock_super_init = mocker.patch.object(
            houdini_package_runner.items.base.BaseFileItem, "__init__"
        )

        if write_back:
            inst = houdini_package_runner.items.digital_asset.ExpandedOperatorType(
                mock_path,
                mock_name,
                write_back=write_back,
                source_file=mock_source_file,
            )
            assert inst._source_file == mock_source_file

        else:
            inst = houdini_package_runner.items.digital_asset.ExpandedOperatorType(
                mock_path, mock_name
            )
            assert inst._source_file is None

        mock_super_init.assert_called_with(mock_path, write_back=write_back)

        assert inst._name == mock_name

    # Non-Public Methods

    @pytest.mark.parametrize("has_sourcefile", (True, False))
    def test__build_python_section_items(self, mocker, init_expanded, has_sourcefile):
        """Test ExpandedOperatorType._build_python_section_items."""
        mock_file1 = mocker.MagicMock(
            spec=houdini_package_runner.items.digital_asset.DigitalAssetPythonSection
        )
        mock_file2 = mocker.MagicMock(
            spec=houdini_package_runner.items.digital_asset.DigitalAssetPythonSection
        )

        mock_init_file = mocker.patch(
            "houdini_package_runner.items.digital_asset.DigitalAssetPythonSection",
            side_effect=[mock_file1, mock_file2],
        )

        mock_source_file = mocker.MagicMock(spec=pathlib.Path)

        mock_path = mocker.MagicMock(spec=pathlib.Path)

        mock_write_back = mocker.MagicMock(spec=bool)

        mocker.patch.object(
            houdini_package_runner.items.digital_asset.ExpandedOperatorType,
            "path",
            mock_path,
        )
        mocker.patch.object(
            houdini_package_runner.items.digital_asset.ExpandedOperatorType,
            "write_back",
            mock_write_back,
        )

        mock_section1 = mocker.MagicMock(spec=pathlib.Path)
        mock_section2 = mocker.MagicMock(spec=pathlib.Path)

        sections = [mock_section1, mock_section2]

        inst = init_expanded()
        inst._source_file = mock_source_file if has_sourcefile else None

        if has_sourcefile:
            expected_display_name1 = mock_source_file / mock_section1.name
            expected_display_name2 = mock_source_file / mock_section2.name

        else:
            expected_display_name1 = mock_path / mock_section1.name
            expected_display_name2 = mock_path / mock_section2.name

        result = inst._build_python_section_items(sections)

        assert result == [mock_file1, mock_file2]

        mock_init_file.assert_has_calls(
            [
                mocker.call(
                    mock_section1,
                    str(expected_display_name1),
                    write_back=mock_write_back,
                ),
                mocker.call(
                    mock_section2,
                    str(expected_display_name2),
                    write_back=mock_write_back,
                ),
            ]
        )

    @pytest.mark.parametrize("cook_exists", (True, False))
    def test__find_python_section_paths(self, mocker, init_expanded, cook_exists):
        """Test ExpandedOperatorType._find_python_sections."""
        mock_section1 = mocker.MagicMock(spec=pathlib.Path)
        mock_section2 = mocker.MagicMock(spec=pathlib.Path)

        mocker.patch.object(
            houdini_package_runner.items.digital_asset.ExpandedOperatorType,
            "_get_extra_python_section_files",
            return_value=[mock_section1, mock_section2],
        )

        mock_path = mocker.MagicMock(spec=pathlib.Path)
        mock_path.__truediv__.return_value.exists.return_value = cook_exists

        mocker.patch.object(
            houdini_package_runner.items.digital_asset.ExpandedOperatorType,
            "path",
            mock_path,
        )

        expected = [mock_section1, mock_section2]

        if cook_exists:
            expected.append(mock_path.__truediv__.return_value)

        inst = init_expanded()

        result = inst._find_python_section_paths()

        assert result == expected

        mock_path.__truediv__.assert_called_with("PythonCook")

    @pytest.mark.parametrize(
        "shelf_exists, has_sourcefile",
        (
            (False, False),
            (True, False),
            (True, True),
        ),
    )
    def test__find_internal_shelf_item(
        self, mocker, init_expanded, shelf_exists, has_sourcefile
    ):
        """Test ExpandedOperatorType._find_internal_shelf_item."""
        mock_path = mocker.MagicMock(spec=pathlib.Path)
        mock_path.__truediv__.return_value.exists.return_value = shelf_exists

        mock_name = mocker.MagicMock(spec=str)
        mock_write_back = mocker.MagicMock(spec=bool)

        mocker.patch.object(
            houdini_package_runner.items.digital_asset.ExpandedOperatorType,
            "path",
            mock_path,
        )
        mocker.patch.object(
            houdini_package_runner.items.digital_asset.ExpandedOperatorType,
            "write_back",
            mock_write_back,
        )
        mocker.patch.object(
            houdini_package_runner.items.digital_asset.ExpandedOperatorType,
            "name",
            mock_name,
        )

        mock_source_file = mocker.MagicMock(spec=pathlib.Path)

        expected_display = (
            str(mock_source_file / "Tools.shelf") if has_sourcefile else None
        )

        mock_init_shelf = mocker.patch(
            "houdini_package_runner.items.digital_asset.ShelfFile"
        )

        inst = init_expanded()
        inst._source_file = mock_source_file if has_sourcefile else None

        result = inst._find_internal_shelf_item()

        if not shelf_exists:
            assert result is None

        else:
            assert result == mock_init_shelf.return_value

            mock_path.__truediv__.assert_called_with("Tools.shelf")

            mock_init_shelf.assert_called_with(
                mock_path.__truediv__.return_value,
                write_back=mock_write_back,
                display_name=expected_display,
                tool_name=mock_name,
            )

    @pytest.mark.parametrize(
        "shelf_exists",
        (True, False),
    )
    def test__gather_items(self, mocker, init_expanded, shelf_exists):
        """Test ExpandedOperatorType._gather_items."""
        mock_path1 = mocker.MagicMock(spec=pathlib.Path)
        mock_path2 = mocker.MagicMock(spec=pathlib.Path)
        python_paths = [mock_path1, mock_path2]
        mocker.patch.object(
            houdini_package_runner.items.digital_asset.ExpandedOperatorType,
            "_find_python_section_paths",
            return_value=python_paths,
        )

        mock_py_file1 = mocker.MagicMock(
            spec=houdini_package_runner.items.filesystem.FileToProcess
        )
        mock_py_file2 = mocker.MagicMock(
            spec=houdini_package_runner.items.filesystem.FileToProcess
        )
        python_items = [mock_py_file1, mock_py_file2]
        mock_build = mocker.patch.object(
            houdini_package_runner.items.digital_asset.ExpandedOperatorType,
            "_build_python_section_items",
            return_value=python_items,
        )

        mock_shelf_item = (
            mocker.MagicMock(spec=houdini_package_runner.items.xml.ShelfFile)
            if shelf_exists
            else None
        )
        mocker.patch.object(
            houdini_package_runner.items.digital_asset.ExpandedOperatorType,
            "_find_internal_shelf_item",
            return_value=mock_shelf_item,
        )

        mock_ds_item = mocker.MagicMock(
            spec=houdini_package_runner.items.dialog_script.DialogScriptItem
        )
        mocker.patch.object(
            houdini_package_runner.items.digital_asset.ExpandedOperatorType,
            "_get_dialog_script_item",
            return_value=mock_ds_item,
        )

        expected = [mock_py_file1, mock_py_file2]

        if shelf_exists:
            expected.append(mock_shelf_item)

        expected.append(mock_ds_item)

        inst = init_expanded()

        result = inst._gather_items()

        assert result == expected

        mock_build.assert_called_with(python_paths)

    @pytest.mark.parametrize("has_sourcefile", (True, False))
    def test__get_dialog_script_item(self, mocker, init_expanded, has_sourcefile):
        """Test ExpandedOperatorType._get_dialog_script_item."""
        mock_path = mocker.MagicMock(spec=pathlib.Path)
        mocker.patch.object(
            houdini_package_runner.items.digital_asset.ExpandedOperatorType,
            "path",
            mock_path,
        )

        mock_write_back = mocker.MagicMock(spec=bool)
        mocker.patch.object(
            houdini_package_runner.items.digital_asset.ExpandedOperatorType,
            "write_back",
            mock_write_back,
        )

        mock_init_ds = mocker.patch(
            "houdini_package_runner.items.digital_asset.DialogScriptItem"
        )

        mocker.patch.object(
            houdini_package_runner.items.digital_asset.ExpandedOperatorType,
            "name",
            "some::path/item",
        )

        inst = init_expanded()
        inst._source_file = (
            pathlib.Path("/some/path/some::source_name") if has_sourcefile else None
        )

        result = inst._get_dialog_script_item()

        assert result == mock_init_ds.return_value

        mock_path.__truediv__.assert_called_with("DialogScript")

        expected_display = (
            "some__source_name_DialogScript"
            if has_sourcefile
            else "some__path_item_DialogScript"
        )
        mock_init_ds.assert_called_with(
            mock_path.__truediv__.return_value,
            expected_display,
            write_back=mock_write_back,
        )

    @pytest.mark.parametrize("options_exist", (True, False))
    def test__get_extra_python_section_files(
        self, mocker, shared_datadir, init_expanded, options_exist
    ):
        """Test ExpandedOperatorType._get_extra_python_section_files."""
        if options_exist:
            path = shared_datadir / "test__get_extra_python_section_files"

        else:
            path = shared_datadir / "does_not_exists"

        mocker.patch.object(
            houdini_package_runner.items.digital_asset.ExpandedOperatorType,
            "path",
            path,
        )

        inst = init_expanded()
        result = inst._get_extra_python_section_files()

        if options_exist:
            assert result == [path / "PythonModule"]

        else:
            assert result == []

    # Properties

    def test_name(self, mocker, init_expanded):
        """Test ExpandedOperatorType.name."""
        mock_name = mocker.MagicMock(spec=str)

        inst = init_expanded()
        inst._name = mock_name

        assert inst.name == mock_name

        with pytest.raises(AttributeError):
            inst.name = "some name"

    # Methods

    @pytest.mark.parametrize(
        "contents_changed, return_codes, expected",
        (
            (True, (0, 0, 0), 0),
            (False, (1, 0, 0), 1),
            (False, (0, 0, 1), 1),
        ),
    )
    def test_process(
        self, mocker, init_expanded, contents_changed, return_codes, expected
    ):
        """Test ExpandedOperatorType.process."""
        mock_runner = mocker.MagicMock(
            spec=houdini_package_runner.runners.base.HoudiniPackageRunner
        )

        mock_item1 = mocker.MagicMock(
            spec=houdini_package_runner.items.filesystem.FileToProcess
        )
        mock_item1.contents_changed = False
        mock_item1.process.return_value = return_codes[0]

        mock_item2 = mocker.MagicMock(
            spec=houdini_package_runner.items.filesystem.FileToProcess
        )
        mock_item2.contents_changed = contents_changed
        mock_item2.process.return_value = return_codes[1]

        mock_item3 = mocker.MagicMock(
            spec=houdini_package_runner.items.filesystem.FileToProcess
        )
        mock_item3.contents_changed = False
        mock_item3.process.return_value = return_codes[2]

        items = [mock_item1, mock_item2, mock_item3]

        mocker.patch.object(
            houdini_package_runner.items.digital_asset.ExpandedOperatorType,
            "_gather_items",
            return_value=items,
        )

        inst = init_expanded()
        inst._contents_changed = False

        result = inst.process(mock_runner)

        assert result == expected

        assert inst._contents_changed == contents_changed

        for item in items:
            item.process.assert_called_with(mock_runner)


class TestDigitalAssetDirectory:
    """Test houdini_package_runner.items.digital_asset.DigitalAssetDirectory."""

    @pytest.mark.parametrize("has_source_file", (False, True))
    def test___init__(self, mocker, has_source_file):
        """Test object initialization."""
        mock_path = mocker.MagicMock(spec=pathlib.Path)
        mock_source_file = mocker.MagicMock(spec=pathlib.PurePath)

        mock_super_init = mocker.patch.object(
            houdini_package_runner.items.base.BaseFileItem, "__init__"
        )

        if has_source_file:
            inst = houdini_package_runner.items.digital_asset.DigitalAssetDirectory(
                mock_path, write_back=True, source_file=mock_source_file
            )

            mock_super_init.assert_called_with(mock_path, write_back=True)

            assert inst._source_file == mock_source_file

        else:
            inst = houdini_package_runner.items.digital_asset.DigitalAssetDirectory(
                mock_path
            )

            mock_super_init.assert_called_with(mock_path, write_back=False)

            assert inst._source_file is None

    @pytest.mark.parametrize("has_source_file", (True, False))
    def test__build_operator_list(self, mocker, init_asset_dir, has_source_file):
        """Test DigitalAssetDirectory._build_operator_list."""
        mock_dir_name1 = mocker.MagicMock(spec=str)
        mock_op_name1 = mocker.MagicMock(spec=str)

        mock_dir_name2 = mocker.MagicMock(spec=str)
        mock_op_name2 = mocker.MagicMock(spec=str)

        dirs = [[mock_dir_name1, mock_op_name1], [mock_dir_name2, mock_op_name2]]

        mocker.patch.object(
            houdini_package_runner.items.digital_asset.DigitalAssetDirectory,
            "_find_operator_dirs",
            return_value=dirs,
        )

        mock_path = mocker.MagicMock(spec=pathlib.Path)
        mocker.patch.object(
            houdini_package_runner.items.digital_asset.DigitalAssetDirectory,
            "path",
            mock_path,
        )

        mock_write_back = mocker.MagicMock(spec=bool)
        mocker.patch.object(
            houdini_package_runner.items.digital_asset.DigitalAssetDirectory,
            "write_back",
            mock_write_back,
        )

        mock_init_expanded = mocker.patch(
            "houdini_package_runner.items.digital_asset.ExpandedOperatorType"
        )

        mock_source_file = mocker.MagicMock(spec=pathlib.PurePath)

        inst = init_asset_dir()
        inst._source_file = mock_source_file if has_source_file else None

        if has_source_file:
            expected_display_names = [
                pathlib.PurePath(f"{mock_source_file}?{mock_op_name1}"),
                pathlib.PurePath(f"{mock_source_file}?{mock_op_name2}"),
            ]
        else:
            expected_display_names = [None, None]

        result = inst._build_operator_list()

        assert len(result) == 2

        mock_init_expanded.assert_has_calls(
            [
                mocker.call(
                    mock_path / mock_dir_name1,
                    mock_op_name1,
                    write_back=mock_write_back,
                    source_file=expected_display_names[0],
                ),
                mocker.call(
                    mock_path / mock_dir_name2,
                    mock_op_name2,
                    write_back=mock_write_back,
                    source_file=expected_display_names[1],
                ),
            ]
        )

    @pytest.mark.parametrize("section_list_exists", (True, False))
    def test__find_operator_dirs(
        self, mocker, shared_datadir, init_asset_dir, section_list_exists
    ):
        """Test DigitalAssetDirectory._find_operator_dirs."""
        path = (
            shared_datadir / "test__find_operator_dirs"
            if section_list_exists
            else shared_datadir
        )

        mocker.patch.object(
            houdini_package_runner.items.digital_asset.DigitalAssetDirectory,
            "path",
            path,
        )

        inst = init_asset_dir()

        if not section_list_exists:
            with pytest.raises(RuntimeError):
                inst._find_operator_dirs()

        else:
            result = inst._find_operator_dirs()

            assert result == [
                [
                    "com.houdinitoolbox_8_8Sop_1cppwrangle_8_81",
                    "com.houdinitoolbox::Sop/cppwrangle::1",
                ]
            ]

    # Methods

    @pytest.mark.parametrize(
        "contents_changed, return_codes, expected",
        (
            (True, (0, 0, 0), 0),
            (False, (0, 1, 0), 1),
        ),
    )
    def test_process(
        self, mocker, init_asset_dir, contents_changed, return_codes, expected
    ):
        """Test DigitalAssetDirectory.process."""
        mock_runner = mocker.MagicMock(
            spec=houdini_package_runner.runners.base.HoudiniPackageRunner
        )

        mock_operator1 = mocker.MagicMock(
            spec=houdini_package_runner.items.digital_asset.ExpandedOperatorType
        )
        mock_operator1.contents_changed = False
        mock_operator1.process.return_value = return_codes[0]

        mock_operator2 = mocker.MagicMock(
            spec=houdini_package_runner.items.digital_asset.ExpandedOperatorType
        )
        mock_operator2.contents_changed = contents_changed
        mock_operator2.process.return_value = return_codes[1]

        mock_operator3 = mocker.MagicMock(
            spec=houdini_package_runner.items.digital_asset.ExpandedOperatorType
        )
        mock_operator3.contents_changed = False
        mock_operator3.process.return_value = return_codes[2]

        operators = [mock_operator1, mock_operator2, mock_operator3]

        mocker.patch.object(
            houdini_package_runner.items.digital_asset.DigitalAssetDirectory,
            "_build_operator_list",
            return_value=operators,
        )

        inst = init_asset_dir()
        inst._contents_changed = False

        result = inst.process(mock_runner)

        assert result == expected

        assert inst._contents_changed == contents_changed

        for operator in operators:
            operator.process.assert_called_with(mock_runner)


class TestBinaryDigitalAssetFile:
    """Test houdini_package_runner.items.digital_asset.BinaryDigitalAssetFile."""

    @pytest.mark.parametrize("return_code", (1, 0))
    def test__collapse_dir(self, mocker, init_binary, return_code):
        """Test BinaryDigitalAssetFile._collapse_dir"""
        mock_target = mocker.MagicMock(spec=pathlib.Path)

        mock_path = mocker.MagicMock(spec=pathlib.Path)
        mocker.patch.object(
            houdini_package_runner.items.digital_asset.BinaryDigitalAssetFile,
            "path",
            mock_path,
        )

        mock_execute = mocker.patch(
            "houdini_package_runner.utils.execute_subprocess_command",
            return_value=return_code,
        )

        inst = init_binary()

        if return_code:
            with pytest.raises(RuntimeError):
                inst._collapse_dir("hotl", mock_target)

        else:
            inst._collapse_dir("hotl", mock_target)

        mock_execute.assert_called_with(
            ["hotl", "-l", str(mock_target), str(mock_path)]
        )

    @pytest.mark.parametrize("return_code", (1, 0))
    def test__extract_file(self, mocker, init_binary, return_code):
        """Test BinaryDigitalAssetFile._extract_file"""
        mock_target = mocker.MagicMock(spec=pathlib.Path)

        mock_path = mocker.MagicMock(spec=pathlib.Path)
        mocker.patch.object(
            houdini_package_runner.items.digital_asset.BinaryDigitalAssetFile,
            "path",
            mock_path,
        )

        mock_execute = mocker.patch(
            "houdini_package_runner.utils.execute_subprocess_command",
            return_value=return_code,
        )

        inst = init_binary()

        if return_code:
            with pytest.raises(RuntimeError):
                inst._extract_file("hotl", mock_target)

        else:
            inst._extract_file("hotl", mock_target)

        mock_execute.assert_called_with(
            ["hotl", "-t", str(mock_target), str(mock_path)]
        )

    @pytest.mark.parametrize(
        "contents_changed, write_back", ((True, True), (True, False), (False, False))
    )
    def test_process(self, mocker, init_binary, contents_changed, write_back):
        """Test BinaryDigitalAssetFile.process."""
        mock_runner = mocker.MagicMock(
            spec=houdini_package_runner.runners.base.HoudiniPackageRunner
        )

        mock_init_dir = mocker.patch(
            "houdini_package_runner.items.digital_asset.DigitalAssetDirectory"
        )

        mock_extract = mocker.patch.object(
            houdini_package_runner.items.digital_asset.BinaryDigitalAssetFile,
            "_extract_file",
        )
        mock_collapse = mocker.patch.object(
            houdini_package_runner.items.digital_asset.BinaryDigitalAssetFile,
            "_collapse_dir",
        )

        mock_path = mocker.MagicMock(spec=pathlib.Path)
        mocker.patch.object(
            houdini_package_runner.items.digital_asset.BinaryDigitalAssetFile,
            "path",
            mock_path,
        )

        mocker.patch.object(
            houdini_package_runner.items.digital_asset.BinaryDigitalAssetFile,
            "write_back",
            write_back,
        )

        target_folder = mock_runner.temp_dir.__truediv__.return_value

        inst = init_binary()
        result = inst.process(mock_runner)

        assert result == mock_init_dir.return_value.process.return_value

        mock_runner.temp_dir.__truediv__.assert_called_with(mock_path.name)

        mock_extract.assert_called_with(mock_runner.hotl_command, target_folder)

        mock_init_dir.assert_called_with(
            target_folder, write_back=write_back, source_file=mock_path
        )
        mock_init_dir.return_value.process.assert_called_with(mock_runner)

        if contents_changed and write_back:
            mock_collapse.assert_called_with(mock_runner.hotl_command, target_folder)

        else:
            mock_collapse.assert_not_called()


@pytest.mark.parametrize("exists", (True, False))
def test_is_expanded_digital_asset_dir(mocker, exists):
    """Test houdini_package_runner.items.digital_asset.is_expanded_digital_asset_dir."""
    mock_path = mocker.MagicMock(spec=pathlib.Path)
    mock_path.__truediv__.return_value.is_file.return_value = exists

    result = houdini_package_runner.items.digital_asset.is_expanded_digital_asset_dir(
        mock_path
    )

    assert result == exists

    mock_path.__truediv__.assert_called_with("Sections.list")
