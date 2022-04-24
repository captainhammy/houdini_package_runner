"""Test the houdini_package_runner.items.filesystem module."""

# =============================================================================
# IMPORTS
# =============================================================================

# Standard Library
import pathlib

# Third Party
import pytest

# Houdini Package Runner
import houdini_package_runner.items.base
import houdini_package_runner.items.filesystem
import houdini_package_runner.runners.base


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def init_dir_item(mocker):
    """Initialize a dummy DirectoryToProcess for testing."""
    mocker.patch.multiple(
        houdini_package_runner.items.filesystem.DirectoryToProcess,
        __init__=lambda x, y, z, w: None,
    )

    def _create():
        return houdini_package_runner.items.filesystem.DirectoryToProcess(
            None, None, None
        )

    return _create


@pytest.fixture
def init_file_item(mocker):
    """Initialize a dummy FileToProcess for testing."""
    mocker.patch.multiple(
        houdini_package_runner.items.filesystem.FileToProcess,
        __init__=lambda x, y, z, w: None,
    )

    def _create():
        return houdini_package_runner.items.filesystem.FileToProcess(None, None, None)

    return _create


@pytest.fixture
def init_houdini_scripts_dir_item(mocker):
    """Initialize a dummy HoudiniScriptsDirectoryItem for testing."""
    mocker.patch.multiple(
        houdini_package_runner.items.filesystem.HoudiniScriptsDirectoryItem,
        __init__=lambda x, y, z, w: None,
    )

    def _create():
        return houdini_package_runner.items.filesystem.HoudiniScriptsDirectoryItem(
            None, None, None
        )

    return _create


# =============================================================================
# TESTS
# =============================================================================


class TestDirectoryToProcess:
    """Test houdini_package_runner.base.filesystem.DirectoryToProcess."""

    @pytest.mark.parametrize("traverse", (None, True, False))
    def test___init__(self, mocker, traverse):
        """Test object initialization."""
        mock_path = mocker.MagicMock(spec=pathlib.Path)
        mock_write_back = mocker.MagicMock(spec=bool)

        mock_super_init = mocker.patch.object(
            houdini_package_runner.items.base.BaseFileItem, "__init__"
        )

        if traverse is not None:
            inst = houdini_package_runner.items.filesystem.DirectoryToProcess(
                mock_path, write_back=mock_write_back, traverse_children=traverse
            )

        else:
            inst = houdini_package_runner.items.filesystem.DirectoryToProcess(
                mock_path, write_back=mock_write_back
            )

        mock_super_init.assert_called_with(mock_path, write_back=mock_write_back)
        assert inst._traverse_children == bool(traverse)

    # Non-Public Methods

    @pytest.mark.parametrize("is_test", (True, False))
    def test__get_child_items(self, shared_datadir, is_test):
        """Test DirectoryToProcess._get_child_items."""
        dir_path = shared_datadir / "test_get_child_items"

        inst = houdini_package_runner.items.filesystem.DirectoryToProcess(dir_path)
        inst.is_test_item = is_test
        result = inst._get_child_items()

        assert len(result) == 3

        if is_test:
            for item in result:
                assert item.is_test_item

    def test__process_children(self, mocker, init_dir_item):
        """Test DirectoryToProcess._process_children."""
        mock_runner = mocker.MagicMock(
            spec=houdini_package_runner.runners.base.HoudiniPackageRunner
        )

        mock_file = mocker.MagicMock(
            spec=houdini_package_runner.items.filesystem.FileToProcess
        )
        mock_file.ignored_builtins = []

        mock_dir = mocker.MagicMock(
            spec=houdini_package_runner.items.filesystem.DirectoryToProcess
        )
        mock_dir.ignored_builtins = []

        mock_get_items = mocker.patch.object(
            houdini_package_runner.items.filesystem.DirectoryToProcess,
            "_get_child_items",
            return_value=(mock_dir, mock_file),
        )

        inst = init_dir_item()

        result = inst._process_children(mock_runner)
        assert result

        mock_get_items.assert_called()

        mock_file.process.assert_called_with(mock_runner)
        mock_dir.process.assert_called_with(mock_runner)

    # Properties

    def test_traverse_children(self, mocker, init_dir_item):
        """Test DirectoryToProcess.traverse_children."""
        mock_traverse = mocker.MagicMock(spec=bool)
        inst = init_dir_item()
        inst._traverse_children = mock_traverse

        assert inst.traverse_children == mock_traverse

    # Methods

    @pytest.mark.parametrize("traverse", (True, False))
    def test_process(self, mocker, init_dir_item, traverse):
        """Test DirectoryToProcess.process."""
        mock_runner = mocker.MagicMock(
            spec=houdini_package_runner.runners.base.HoudiniPackageRunner
        )

        mock_path = mocker.MagicMock(spec=pathlib.Path)

        inst = init_dir_item()
        mocker.patch.object(
            houdini_package_runner.items.filesystem.DirectoryToProcess,
            "path",
            mocker.PropertyMock(return_value=mock_path),
        )

        mocker.patch.object(
            houdini_package_runner.items.filesystem.DirectoryToProcess,
            "traverse_children",
            mocker.PropertyMock(return_value=traverse),
        )

        mock_process = mocker.patch.object(
            houdini_package_runner.items.filesystem.DirectoryToProcess,
            "_process_children",
        )

        result = inst.process(mock_runner)

        if traverse:
            assert result == mock_process.return_value
            mock_process.assert_called_with(mock_runner)
        else:
            assert result == mock_runner.process_path.return_value
            mock_runner.process_path.assert_called_with(mock_path, inst)


class TestFileToProcess:
    """Test houdini_package_runner.base.filesystem.FileToProcess."""

    @pytest.mark.parametrize("display_name", (None, "display_name"))
    def test___init__(self, mocker, display_name):
        """Test object initialization."""
        mock_path = mocker.MagicMock(spec=pathlib.Path)
        mock_write_back = mocker.MagicMock(spec=bool)

        mock_super_init = mocker.patch.object(
            houdini_package_runner.items.base.BaseFileItem, "__init__"
        )

        if display_name is not None:
            inst = houdini_package_runner.items.filesystem.FileToProcess(
                mock_path, write_back=mock_write_back, display_name=display_name
            )

        else:
            inst = houdini_package_runner.items.filesystem.FileToProcess(
                mock_path, write_back=mock_write_back
            )

        mock_super_init.assert_called_with(mock_path, write_back=mock_write_back)
        assert inst._display_name == display_name

    # Properties

    def test_display_name(self, mocker, init_file_item):
        """Test FileToProcess.display_name."""
        mock_display_name = mocker.MagicMock(spec=str)

        inst = init_file_item()
        inst._display_name = mock_display_name

        assert inst.display_name == mock_display_name

        mock_set_display_name = mocker.MagicMock(spec=str)
        inst.display_name = mock_set_display_name

        assert inst._display_name == mock_set_display_name

    # Methods

    @pytest.mark.parametrize("contents_changed", (True, False))
    def test_process(self, mocker, init_file_item, contents_changed):
        """Test FileToProcess.process."""
        mock_runner = mocker.MagicMock(
            spec=houdini_package_runner.runners.base.HoudiniPackageRunner
        )

        mock_hash1 = mocker.MagicMock(spec=bytes)
        mock_hash2 = mocker.MagicMock(spec=bytes)

        results = (
            (mock_hash1, mock_hash2) if contents_changed else (mock_hash1, mock_hash1)
        )

        mock_compute = mocker.patch(
            "houdini_package_runner.items.filesystem.compute_file_hash",
            side_effect=results,
        )

        mock_path = mocker.MagicMock(spec=pathlib.Path)

        inst = init_file_item()
        mocker.patch.object(
            houdini_package_runner.items.filesystem.FileToProcess,
            "path",
            mocker.PropertyMock(return_value=mock_path),
        )

        result = inst.process(mock_runner)

        assert result == mock_runner.process_path.return_value

        assert inst.contents_changed == contents_changed

        mock_runner.process_path.assert_called_with(mock_path, inst)
        mock_compute.assert_has_calls(
            [
                mocker.call(mock_path),
                mocker.call(mock_path),
            ]
        )


class TestHoudiniScriptsDirectoryItem:
    """Test houdini_package_runner.base.filesystem.HoudiniScriptsDirectoryItem."""

    def test__get_child_items(self, mocker, init_houdini_scripts_dir_item):
        """Test HoudiniScriptsDirectoryItem._get_child_items."""
        mock_file = mocker.MagicMock(
            spec=houdini_package_runner.items.filesystem.FileToProcess
        )
        mock_file.ignored_builtins = []

        mock_dir = mocker.MagicMock(
            spec=houdini_package_runner.items.filesystem.DirectoryToProcess
        )
        mock_dir.ignored_builtins = []

        mock_super_get = mocker.patch.object(
            houdini_package_runner.items.filesystem.DirectoryToProcess,
            "_get_child_items",
            return_value=(mock_dir, mock_file),
        )

        inst = init_houdini_scripts_dir_item()

        inst._get_child_items()

        mock_super_get.assert_called()
        assert mock_file.ignored_builtins == ["kwargs"]
        assert mock_dir.ignored_builtins == []


class TestPythonPackageDirectoryItem:
    """Test houdini_package_runner.base.filesystem.PythonPackageDirectoryItem."""

    def test___init__(self, mocker):
        """Test object initialization."""
        mock_path = mocker.MagicMock(spec=pathlib.Path)
        mock_write_back = mocker.MagicMock(spec=bool)

        mock_super_init = mocker.patch.object(
            houdini_package_runner.items.filesystem.DirectoryToProcess, "__init__"
        )

        houdini_package_runner.items.filesystem.PythonPackageDirectoryItem(
            mock_path, write_back=mock_write_back
        )

        mock_super_init.assert_called_with(mock_path, write_back=mock_write_back)


@pytest.mark.parametrize(
    "file_name, expected",
    [
        ("python_file.py", b"\xd4\x1d\x8c\xd9\x8f\x00\xb2\x04\xe9\x80\t\x98\xec\xf8B~"),
        ("ls_script", b"k\x81\xfd\xd0$\x0c\xaf\x90\x147\xc1-C\xb6\xb9\x06"),
        ("no_shbang_script", b"be\xb2+fP-p\xd5\xf0\x04\xf0\x828\xac<"),
        ("decode_error.hip", b"}\xb2\x0fK\x9b\xffK[\x07\xd0g\xedpR\x1bq"),
        ("python_script", b"(\xb3V\x12\xb1E\xc3Lgh\x17\xcei\xfb\xfe\xb6"),
        ("hython_script", b"\x1a?\x00\x1c\x1d\xb9\xd0i\xf2\x1e\x0ep\xce\xa7x\x90"),
    ],
)
def test_compute_file_hash(shared_datadir, file_name, expected):
    """Test houdini_package_runner.items.filesystem.compute_file_hash."""
    file_path = shared_datadir / "test_is_python_file" / file_name

    result = houdini_package_runner.items.filesystem.compute_file_hash(file_path)

    assert result == expected


@pytest.mark.parametrize(
    "file_name, bins, expected",
    [
        ("python_file.py", None, True),
        ("python_file.pyc", None, False),
        ("ls_script", None, False),
        ("no_shbang_script", None, False),
        ("decode_error.hip", None, False),
        ("python_script", None, True),
        ("hython_script", None, False),
        ("hython_script", ["hython"], True),
        ("hython_script", ["python", "hython"], True),
    ],
)
def test_is_python_file(shared_datadir, file_name, bins, expected):
    """Test houdini_package_runner.items.filesystem.is_python_file."""
    file_path = shared_datadir / "test_is_python_file" / file_name
    result = houdini_package_runner.items.filesystem.is_python_file(
        file_path, python_bins=bins
    )

    assert result == expected
