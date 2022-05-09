"""Test the houdini_package_runner.discoverers.base module."""

# =============================================================================
# IMPORTS
# =============================================================================

# Standard Library
import pathlib

# Third Party
import pytest

# Houdini Package Runner
import houdini_package_runner.discoverers.base
import houdini_package_runner.items.filesystem

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def init_discoverer(mocker):
    """Initialize a dummy HoudiniPackageRunner for testing."""
    mocker.patch.multiple(
        houdini_package_runner.discoverers.base.BaseItemDiscoverer,
        __abstractmethods__=set(),
        __init__=lambda x, y, z: None,
    )

    def _create():
        return houdini_package_runner.discoverers.base.BaseItemDiscoverer(None, None)

    return _create


# =============================================================================
# TESTS
# =============================================================================


class TestBaseItemDiscoverer:
    """Test houdini_package_runner.discoverers.base.BaseItemDiscoverer."""

    # Object construction

    @pytest.mark.parametrize("has_items", (False, True))
    def test___init__(self, mocker, remove_abstract_methods, has_items):
        """Test object initialization."""
        remove_abstract_methods(
            houdini_package_runner.discoverers.base.BaseItemDiscoverer
        )
        mock_path = mocker.MagicMock(spec=pathlib.Path)

        items = []

        if has_items:
            items = [
                mocker.MagicMock(
                    spec=houdini_package_runner.items.filesystem.FileToProcess
                )
            ]
            inst = houdini_package_runner.discoverers.base.BaseItemDiscoverer(
                mock_path, items=items
            )

        else:
            inst = houdini_package_runner.discoverers.base.BaseItemDiscoverer(mock_path)

        assert inst._path == mock_path
        assert inst._items == items

    # Properties

    def test_items(self, mocker, init_discoverer):
        """Test BaseItemDiscoverer.items."""
        mock_items = mocker.MagicMock(spec=list)

        inst = init_discoverer()
        inst._items = mock_items

        assert inst.items == mock_items

    def test_temp_dir(self, mocker, init_discoverer):
        """Test BaseItemDiscoverer.temp_dir."""
        mock_path = mocker.MagicMock(spec=pathlib.Path)

        inst = init_discoverer()
        inst._path = mock_path

        assert inst.path == mock_path
