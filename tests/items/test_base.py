"""Test the houdini_package_runner.base.item module."""

# =============================================================================
# IMPORTS
# =============================================================================

# Standard Library
import pathlib

# Third Party
import pytest

# Houdini Package Runner
import houdini_package_runner.items.base

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def init_base_item(mocker):
    """Initialize a dummy BaseItem for testing."""
    mocker.patch.multiple(
        houdini_package_runner.items.base.BaseItem,
        __abstractmethods__=set(),
        __init__=lambda x, y: None,
    )

    def _create():
        return houdini_package_runner.items.base.BaseItem(None)

    return _create


@pytest.fixture
def init_base_file_item(mocker):
    """Initialize a dummy BaseFileItem for testing."""
    mocker.patch.multiple(
        houdini_package_runner.items.base.BaseFileItem,
        __abstractmethods__=set(),
        __init__=lambda x, y, z: None,
    )

    def _create():
        return houdini_package_runner.items.base.BaseFileItem(None, None)

    return _create


# =============================================================================
# TESTS
# =============================================================================


class TestBaseItem:
    """Test houdini_package_runner.base.item.BaseItem."""

    # Object construction

    @pytest.mark.parametrize("write_back", (None, False, True))
    def test___init__(self, remove_abstract_methods, write_back):
        """Test object initialization."""
        remove_abstract_methods(houdini_package_runner.items.base.BaseItem)

        if write_back is not None:
            inst = houdini_package_runner.items.base.BaseItem(write_back=write_back)

        else:
            inst = houdini_package_runner.items.base.BaseItem()

        assert not inst._contents_changed
        assert isinstance(inst._ignored_builtins, list)
        assert not inst._ignored_builtins
        assert not inst._is_single_line
        assert not inst._is_test_item
        assert inst.write_back == bool(write_back)

    # Properties

    def test_contents_changed(self, init_base_item):
        """Test BaseItem.contents_changed."""
        inst = init_base_item()
        inst._contents_changed = False

        assert not inst.contents_changed

        inst.contents_changed = True
        assert inst._contents_changed

    def test_ignored_builtins(self, mocker, init_base_item):
        """Test BaseItem.ignored_builtins."""
        mock_builtin = mocker.MagicMock(spec=str)
        inst = init_base_item()
        inst._ignored_builtins = [mock_builtin]

        assert inst.ignored_builtins == [mock_builtin]

        with pytest.raises(AttributeError):
            inst.ignored_builtins = []

    def test_is_single_line(self, mocker, init_base_item):
        """Test BaseItem.is_single_line."""
        mock_single = mocker.MagicMock(spec=bool)

        inst = init_base_item()
        inst._is_single_line = mock_single

        assert inst.is_single_line == mock_single

        with pytest.raises(AttributeError):
            inst.is_single_line = True

    def test_is_test_item(self, init_base_item):
        """Test BaseItem.is_test_item."""
        inst = init_base_item()
        inst._is_test_item = False

        assert not inst.is_test_item

        inst.is_test_item = True
        assert inst.is_test_item

    def test_write_back(self, init_base_item):
        """Test BaseItem.write_back."""
        inst = init_base_item()
        inst._write_back = False

        assert not inst.write_back

        inst.write_back = True

        assert inst._write_back


class TestBaseFileItem:
    """Test houdini_package_runner.base.item.BaseFileItem."""

    # Object construction

    @pytest.mark.parametrize("default_args", (False, True))
    def test___init__(self, mocker, remove_abstract_methods, default_args):
        """Test object initialization."""
        mock_path = mocker.MagicMock(spec=pathlib.Path)
        mock_write_back = mocker.MagicMock(spec=bool)

        remove_abstract_methods(houdini_package_runner.items.base.BaseFileItem)

        mock_super_init = mocker.patch.object(
            houdini_package_runner.items.base.BaseItem, "__init__"
        )

        if default_args:
            inst = houdini_package_runner.items.base.BaseFileItem(mock_path)

            mock_super_init.assert_called_with(write_back=False)

        else:
            inst = houdini_package_runner.items.base.BaseFileItem(
                mock_path, write_back=mock_write_back
            )

            mock_super_init.assert_called_with(write_back=mock_write_back)

        assert inst._path == mock_path

    # Properties

    def test_path(self, mocker, init_base_file_item):
        """Test BaseFileItem.path."""
        mock_path = mocker.MagicMock(spec=pathlib.Path)

        inst = init_base_file_item()
        inst._path = mock_path

        assert inst.path == mock_path
