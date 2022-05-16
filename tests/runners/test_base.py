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
import houdini_package_runner.config
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

    @pytest.mark.parametrize("pass_optional", (False, True))
    def test___init__(self, mocker, remove_abstract_methods, pass_optional):
        """Test object initialization."""
        remove_abstract_methods(
            houdini_package_runner.runners.base.HoudiniPackageRunner
        )

        mock_write_back = mocker.MagicMock(spec=bool) if pass_optional else False
        mock_discoverer = mocker.MagicMock(spec=BaseItemDiscoverer)
        mock_mkdtemp = mocker.patch("tempfile.mkdtemp", return_value="/path/to/temp")

        mock_config = (
            mocker.MagicMock(spec=houdini_package_runner.config.PackageRunnerConfig)
            if pass_optional
            else None
        )

        mock_init_config = mocker.patch(
            "houdini_package_runner.runners.base.PackageRunnerConfig"
        )

        if pass_optional:
            inst = houdini_package_runner.runners.base.HoudiniPackageRunner(
                mock_discoverer, write_back=mock_write_back, runner_config=mock_config
            )

        else:
            inst = houdini_package_runner.runners.base.HoudiniPackageRunner(
                mock_discoverer
            )

        assert inst._discoverer == mock_discoverer
        assert not inst._extra_args
        assert inst._hotl_command == "hotl"
        assert inst._temp_dir == pathlib.Path(mock_mkdtemp.return_value)
        assert not inst._verbose
        assert inst._write_back == mock_write_back

        if pass_optional:
            assert inst._config == mock_config

        else:
            assert inst._config == mock_init_config.return_value

    # Properties

    def test_config(self, mocker, init_runner):
        """Test HoudiniPackageRunner.config."""
        mock_config = mocker.MagicMock(
            spec=houdini_package_runner.config.BaseRunnerConfig
        )

        inst = init_runner()
        inst._config = mock_config

        assert inst.config == mock_config

        with pytest.raises(AttributeError):
            inst.config = None

    def test_discoverer(self, mocker, init_runner):
        """Test HoudiniPackageRunner.discoverer."""
        mock_discoverer = mocker.MagicMock(spec=BaseItemDiscoverer)

        inst = init_runner()
        inst._discoverer = mock_discoverer

        assert inst.discoverer == mock_discoverer

        with pytest.raises(AttributeError):
            inst.discoverer = None

    def test_extra_args(self, mocker, init_runner):
        """Test HoudiniPackageRunner.extra_args."""
        mock_args = mocker.MagicMock(spec=list)

        inst = init_runner()
        inst._extra_args = mock_args

        assert inst.extra_args == mock_args

        with pytest.raises(AttributeError):
            inst.extra_args = []

    def test_hotl_command(self, mocker, init_runner):
        """Test HoudiniPackageRunner.hotl_command."""
        mock_command = mocker.MagicMock(spec=str)

        inst = init_runner()
        inst._hotl_command = mock_command

        assert inst.hotl_command == mock_command

        with pytest.raises(AttributeError):
            inst.hotl_command = None

    def test_temp_dir(self, mocker, init_runner):
        """Test HoudiniPackageRunner.temp_dir."""
        mock_path = mocker.MagicMock(spec=pathlib.Path)

        inst = init_runner()
        inst._temp_dir = mock_path

        assert inst.temp_dir == mock_path

        with pytest.raises(AttributeError):
            inst.temp_dir = None

    def test_verbose(self, mocker, init_runner):
        """Test HoudiniPackageRunner.verbose."""
        mock_verbose = mocker.MagicMock(spec=bool)

        inst = init_runner()
        inst._verbose = mock_verbose

        assert inst.verbose == mock_verbose

        with pytest.raises(AttributeError):
            inst.temp_dir = False

    def test_write_back(self, mocker, init_runner):
        """Test HoudiniPackageRunner.write_back."""
        mock_write_back = mocker.MagicMock(spec=bool)

        inst = init_runner()
        inst._write_back = mock_write_back

        assert inst.write_back == mock_write_back

        with pytest.raises(AttributeError):
            inst.write_back = False

    # Methods

    @pytest.mark.parametrize("has_hotl", (True, False))
    def test_init_args_options(self, mocker, init_runner, has_hotl):
        """Test HoudiniPackageRunner.init_args_options."""
        mock_verbose = mocker.MagicMock(spec=bool)
        mock_list = mocker.MagicMock(spec=bool)
        mock_hotl = mocker.MagicMock(spec=str)

        namespace = argparse.Namespace()
        namespace.verbose = mock_verbose
        namespace.list_items = mock_list

        if has_hotl:
            namespace.hotl_command = mock_hotl

        inst = init_runner()

        inst.init_args_options(namespace, [])

        assert inst._verbose == mock_verbose

        if has_hotl:
            assert inst._hotl_command == mock_hotl

    @pytest.mark.parametrize(
        "list_items, write_back, return_codes, expected",
        (
            (True, False, (0, 0), 0),
            (False, False, (0, 0), 0),
            (False, True, (0, 1), 1),
            (False, True, (1, 0), 1),
        ),
    )
    def test_run(
        self, mocker, init_runner, list_items, write_back, return_codes, expected
    ):
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
        inst._list_items = list_items
        inst._write_back = write_back

        result = inst.run()
        assert result == expected

        if not list_items:
            mock_file.process.assert_called_with(inst)
            mock_dir.process.assert_called_with(inst)

        if write_back:
            assert mock_file.write_back
            assert mock_dir.write_back
