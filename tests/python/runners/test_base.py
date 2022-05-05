"""Test the houdini_package_runner.runners.base module."""

# =============================================================================
# IMPORTS
# =============================================================================

# Standard Library
import argparse
import pathlib

# Third Party
import pytest

# Houdini Package Runner
import houdini_package_runner.items.filesystem
import houdini_package_runner.runners.base
from houdini_package_runner.discoverers.base import BaseItemDiscoverer

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def init_runner(mocker):
    """Initialize a dummy HoudiniPackageRunner for testing."""
    mocker.patch.multiple(
        houdini_package_runner.runners.base.HoudiniPackageRunner,
        __abstractmethods__=set(),
        __init__=lambda x, y, z: None,
    )

    def _create():
        return houdini_package_runner.runners.base.HoudiniPackageRunner(None, None)

    return _create


# =============================================================================
# TESTS
# =============================================================================


class TestHoudiniPackageRunner:
    """Test houdini_package_runner.runners.base.HoudiniPackageRunner."""

    # Object construction

    @pytest.mark.parametrize("write_back", (None, False, True))
    def test___init__(self, mocker, remove_abstract_methods, write_back):
        """Test object initialization."""
        remove_abstract_methods(
            houdini_package_runner.runners.base.HoudiniPackageRunner
        )

        mock_discoverer = mocker.MagicMock(spec=BaseItemDiscoverer)
        mock_mkdtemp = mocker.patch("tempfile.mkdtemp", return_value="/path/to/temp")

        if write_back is not None:
            inst = houdini_package_runner.runners.base.HoudiniPackageRunner(
                mock_discoverer, write_back=write_back
            )

        else:
            inst = houdini_package_runner.runners.base.HoudiniPackageRunner(
                mock_discoverer
            )

        assert inst._discoverer == mock_discoverer
        assert inst._hotl_command == "hotl"
        assert inst._temp_dir == pathlib.Path(mock_mkdtemp.return_value)
        assert not inst._verbose
        assert inst._write_back == bool(write_back)

    # Properties

    def test_discoverer(self, mocker, init_runner):
        """Test HoudiniPackageRunner.discoverer."""
        mock_discoverer = mocker.MagicMock(spec=BaseItemDiscoverer)

        inst = init_runner()
        inst._discoverer = mock_discoverer

        assert inst.discoverer == mock_discoverer

    def test_hotl_command(self, mocker, init_runner):
        """Test HoudiniPackageRunner.hotl_command."""
        mock_command = mocker.MagicMock(spec=str)

        inst = init_runner()
        inst._hotl_command = mock_command

        assert inst.hotl_command == mock_command

    def test_temp_dir(self, mocker, init_runner):
        """Test HoudiniPackageRunner.temp_dir."""
        mock_path = mocker.MagicMock(spec=pathlib.Path)

        inst = init_runner()
        inst._temp_dir = mock_path

        assert inst.temp_dir == mock_path

    def test_verbose(self, mocker, init_runner):
        """Test HoudiniPackageRunner.verbose."""
        mock_verbose = mocker.MagicMock(spec=bool)

        inst = init_runner()
        inst._verbose = mock_verbose

        assert inst.verbose == mock_verbose

    def test_write_back(self, mocker, init_runner):
        """Test HoudiniPackageRunner.write_back."""
        mock_write_back = mocker.MagicMock(spec=bool)

        inst = init_runner()
        inst._write_back = mock_write_back

        assert inst.write_back == mock_write_back

    # Methods

    @pytest.mark.parametrize("has_hotl", (True, False))
    def test_init_args_options(self, mocker, init_runner, has_hotl):
        """Test HoudiniPackageRunner.init_args_options."""
        mock_verbose = mocker.MagicMock(spec=bool)
        mock_hotl = mocker.MagicMock(spec=str)

        namespace = argparse.Namespace()
        namespace.verbose = mock_verbose

        if has_hotl:
            namespace.hotl_command = mock_hotl

        inst = init_runner()

        inst.init_args_options(namespace, [])

        assert inst._verbose == mock_verbose

        if has_hotl:
            assert inst._hotl_command == mock_hotl

    @pytest.mark.parametrize(
        "write_back, return_codes, expected",
        (
            (False, (0, 0), 0),
            (True, (0, 1), 1),
            (True, (1, 0), 1),
        ),
    )
    def test_run(self, mocker, init_runner, write_back, return_codes, expected):
        """Test HoudiniPackageRunner.run."""
        mock_file = mocker.MagicMock(
            spec=houdini_package_runner.items.filesystem.FileToProcess
        )
        mock_file.write_back = False
        mock_file.process.return_value = return_codes[0]

        mock_dir = mocker.MagicMock(
            spec=houdini_package_runner.items.filesystem.DirectoryToProcess
        )
        mock_dir.write_back = False
        mock_dir.process.return_value = return_codes[1]

        mock_discoverer = mocker.MagicMock(spec=BaseItemDiscoverer)
        type(mock_discoverer).items = [mock_file, mock_dir]

        mocker.patch.object(
            houdini_package_runner.runners.base.HoudiniPackageRunner,
            "discoverer",
            mock_discoverer,
        )

        inst = init_runner()
        inst._write_back = write_back

        result = inst.run()
        assert result == expected

        mock_file.process.assert_called_with(inst)
        mock_dir.process.assert_called_with(inst)

        if write_back:
            assert mock_file.write_back
            assert mock_dir.write_back
