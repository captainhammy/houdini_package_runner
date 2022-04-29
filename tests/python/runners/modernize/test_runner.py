"""Test the houdini_package_runner.runners.modernize.runner module."""

# =============================================================================
# IMPORTS
# =============================================================================

# Standard Library
import argparse
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
import houdini_package_runner.runners.modernize.runner
from houdini_package_runner.discoverers.base import BaseItemDiscoverer


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def init_runner(mocker):
    """Initialize a dummy ModernizeRunner for testing."""
    mocker.patch.multiple(
        houdini_package_runner.runners.modernize.runner.ModernizeRunner,
        __init__=lambda x, y: None,
    )

    def _create():
        return houdini_package_runner.runners.modernize.runner.ModernizeRunner(None)

    return _create


# =============================================================================
# TESTS
# =============================================================================


class TestModernizeRunner:
    """Test houdini_package_runner.runners.modernize.runner.ModernizeRunner."""

    def test___init__(self, mocker):
        """Test object initialization."""
        mock_discoverer = mocker.MagicMock(spec=BaseItemDiscoverer)

        mock_super_init = mocker.patch.object(
            houdini_package_runner.runners.modernize.runner.HoudiniPackageRunner,
            "__init__",
        )

        inst = houdini_package_runner.runners.modernize.runner.ModernizeRunner(
            mock_discoverer
        )

        assert inst._extra_args == []

        mock_super_init.assert_called_with(mock_discoverer, write_back=True)

    # Properties

    def test_extra_args(self, mocker, init_runner):
        """Test ModernizeRunner.extra_args."""
        mock_args = mocker.MagicMock(spec=list)

        inst = init_runner()
        inst._extra_args = mock_args

        assert inst.extra_args == mock_args

        with pytest.raises(AttributeError):
            inst.extra_args = []

    # Methods

    @pytest.mark.parametrize("pass_parser", (True, False))
    def test_build_parser(self, mocker, pass_parser):
        """Test ModernizeRunner.build_parser."""
        mock_build = mocker.patch("houdini_package_runner.parser.build_common_parser")

        if pass_parser:
            mock_parser = mocker.MagicMock(spec=argparse.ArgumentParser)

            result = houdini_package_runner.runners.modernize.runner.ModernizeRunner.build_parser(
                parser=mock_parser
            )
            assert result == mock_parser

            mock_build.assert_not_called()

        else:
            result = (
                houdini_package_runner.runners.modernize.runner.ModernizeRunner.build_parser()
            )

            assert result == mock_build.return_value

    def test_init_args_options(self, mocker, init_runner):
        """Test ModernizeRunner.init_args_options."""
        mock_namespace = mocker.MagicMock(spec=argparse.Namespace)
        mock_extra_args = mocker.MagicMock(spec=list)

        mock_super_init = mocker.patch.object(
            houdini_package_runner.runners.modernize.runner.HoudiniPackageRunner,
            "init_args_options",
        )

        inst = init_runner()

        inst.init_args_options(mock_namespace, mock_extra_args)

        mock_super_init.assert_called_with(mock_namespace, mock_extra_args)

        assert inst._extra_args == mock_extra_args

    @pytest.mark.parametrize(
        "is_dialog_script",
        (True, False),
    )
    def test_process_path(self, mocker, init_runner, is_dialog_script):
        """Test ModernizeRunner.process_path."""
        mock_path = mocker.MagicMock(spec=pathlib.Path)

        if is_dialog_script:
            mock_item = mocker.MagicMock(
                spec=houdini_package_runner.items.dialog_script.DialogScriptInternalItem
            )

        else:
            mock_item = mocker.MagicMock(
                spec=houdini_package_runner.items.filesystem.FileToProcess
            )

        mock_execute = mocker.patch(
            "houdini_package_runner.utils.execute_subprocess_command"
        )

        extra_args = ["--flag", "arg"]

        mocker.patch.object(
            houdini_package_runner.runners.modernize.runner.ModernizeRunner,
            "extra_args",
            extra_args,
        )

        mock_verbose = mocker.MagicMock(spec=bool)

        inst = init_runner()
        inst._verbose = mock_verbose

        inst.process_path(mock_path, mock_item)

        expected_args = (
            ["python-modernize", "--write", "--nobackups"]
            + extra_args
            + [str(mock_path)]
        )

        if is_dialog_script:
            expected_args.insert(5, "import,print")
            expected_args.insert(5, "--nofix")

        mock_execute.assert_called_with(expected_args, verbose=mock_verbose)


def test_main(mocker):
    """Test houdini_package_runner.runners.modernize.runner.main."""
    mock_parsed = mocker.MagicMock(spec=argparse.Namespace)
    mock_unknown = mocker.MagicMock(spec=list)

    mock_parser = mocker.MagicMock(spec=argparse.ArgumentParser)
    mock_parser.parse_known_args.return_value = (mock_parsed, mock_unknown)

    mock_discoverer = mocker.MagicMock(spec=BaseItemDiscoverer)
    mock_init = mocker.patch(
        "houdini_package_runner.runners.modernize.runner.package.init_standard_discoverer",
        return_value=mock_discoverer,
    )

    mock_runner = mocker.MagicMock(
        spec=houdini_package_runner.runners.modernize.runner.ModernizeRunner
    )

    mock_runner_init = mocker.patch(
        "houdini_package_runner.runners.modernize.runner.ModernizeRunner",
        return_value=mock_runner,
    )
    mock_runner_init.build_parser.return_value = mock_parser

    houdini_package_runner.runners.modernize.runner.main()

    mock_init.assert_called_with(mock_parsed)

    mock_runner_init.assert_called_with(mock_discoverer)
    mock_runner.init_args_options.assert_called_with(mock_parsed, mock_unknown)
    mock_runner.run.assert_called()
