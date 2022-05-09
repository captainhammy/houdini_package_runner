"""Test the houdini_package_runner.runners.flake8.runner module."""

# =============================================================================
# IMPORTS
# =============================================================================

# Standard Library
import argparse
import copy
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
import houdini_package_runner.runners.flake8.runner
from houdini_package_runner.discoverers.base import BaseItemDiscoverer

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def init_runner(mocker):
    """Initialize a dummy Flake8Runner for testing."""
    mocker.patch.multiple(
        houdini_package_runner.runners.flake8.runner.Flake8Runner,
        __init__=lambda x, y: None,
    )

    def _create():
        return houdini_package_runner.runners.flake8.runner.Flake8Runner(None)

    return _create


# =============================================================================
# TESTS
# =============================================================================


class TestFlake8Runner:
    """Test houdini_package_runner.runners.flake8.runner.Flake8Runner."""

    def test___init__(self, mocker):
        """Test object initialization."""
        mock_discoverer = mocker.MagicMock(spec=BaseItemDiscoverer)

        mock_super_init = mocker.patch.object(
            houdini_package_runner.runners.flake8.runner.HoudiniPackageRunner,
            "__init__",
        )

        inst = houdini_package_runner.runners.flake8.runner.Flake8Runner(
            mock_discoverer
        )

        assert inst._ignored == []
        assert inst._extra_args == []

        mock_super_init.assert_called_with(mock_discoverer, write_back=True)

    # Properties

    def test_extra_args(self, mocker, init_runner):
        """Test Flake8Runner.extra_args."""
        mock_args = mocker.MagicMock(spec=list)

        inst = init_runner()
        inst._extra_args = mock_args

        assert inst.extra_args == mock_args

        with pytest.raises(AttributeError):
            inst.extra_args = []

    # Methods

    @pytest.mark.parametrize("pass_parser", (True, False))
    def test_build_parser(self, mocker, pass_parser):
        """Test Flake8Runner.build_parser."""
        mock_parser = mocker.MagicMock(spec=argparse.ArgumentParser)

        mock_build = mocker.patch(
            "houdini_package_runner.parser.build_common_parser",
            return_value=mock_parser,
        )

        if pass_parser:
            result = (
                houdini_package_runner.runners.flake8.runner.Flake8Runner.build_parser(
                    parser=mock_parser
                )
            )

            mock_build.assert_not_called()

        else:
            result = (
                houdini_package_runner.runners.flake8.runner.Flake8Runner.build_parser()
            )
            mock_build.assert_called()

        assert result == mock_parser

        result.add_argument.assert_has_calls(
            [
                mocker.call(
                    "--config",
                    action="store",
                    help="Specify a configuration file",
                ),
                mocker.call("--ignore", action="store", help="Tests to ignore."),
            ]
        )

    @pytest.mark.parametrize("has_options_set", (True, False))
    def test_init_args_options(self, mocker, init_runner, has_options_set):
        """Test Flake8Runner.init_args_options."""
        mock_namespace = mocker.MagicMock()

        if has_options_set:
            mock_namespace.config = "config_path"
            mock_namespace.ignore = "foo,bar"

        else:
            mock_namespace.config = None
            mock_namespace.ignore = None

        extra_args = ["arg1", "arg2"]

        expected_extra_args = copy.copy(extra_args)

        if has_options_set:
            expected_extra_args.insert(0, f"--config={mock_namespace.config}")

        mock_super_init = mocker.patch.object(
            houdini_package_runner.runners.flake8.runner.HoudiniPackageRunner,
            "init_args_options",
        )

        inst = init_runner()
        inst._ignored = []

        inst.init_args_options(mock_namespace, extra_args)

        mock_super_init.assert_called_with(mock_namespace, extra_args)

        assert inst._extra_args == extra_args

        if has_options_set:
            assert inst._ignored == ["foo", "bar"]

        else:
            assert inst._ignored == []

    @pytest.mark.parametrize(
        "has_ignored, item_type, has_builtins",
        (
            (
                True,
                houdini_package_runner.items.dialog_script.DialogScriptInternalItem,
                True,
            ),
            (False, houdini_package_runner.items.xml.MenuFile, False),
            (False, houdini_package_runner.items.filesystem.FileToProcess, False),
        ),
    )
    def test_process_path(
        self, mocker, init_runner, has_ignored, item_type, has_builtins
    ):
        """Test Flake8Runner.process_path."""
        mock_path = mocker.MagicMock(spec=pathlib.Path)

        mock_item = mocker.MagicMock(spec=item_type)

        mock_item.ignored_builtins = ["hou"] if has_builtins else []

        mock_add_flags = mocker.patch(
            "houdini_package_runner.utils.add_or_append_to_flags"
        )

        mock_execute = mocker.patch(
            "houdini_package_runner.utils.execute_subprocess_command"
        )

        extra_args = ["--flag", "arg"]

        mocker.patch.object(
            houdini_package_runner.runners.flake8.runner.Flake8Runner,
            "extra_args",
            extra_args,
        )

        mock_verbose = mocker.MagicMock(spec=bool)

        expected_ignored = []

        inst = init_runner()
        inst._ignored = []
        inst._verbose = mock_verbose

        if has_ignored:
            inst._ignored = ["A123"]
            expected_ignored = inst._ignored

        inst.process_path(mock_path, mock_item)

        expected_args = ["flake8"]

        if isinstance(mock_item, houdini_package_runner.items.xml.XMLBase):
            expected_args.append("--max-line-length=150")
            expected_ignored.append("W292")

        elif isinstance(
            mock_item,
            houdini_package_runner.items.dialog_script.DialogScriptInternalItem,
        ):
            expected_ignored.extend(["W292", "F706"])

        if has_builtins:
            # Only do assert_called() here as the command list will change and be inaccurate.
            mock_add_flags.assert_called()

        if expected_ignored:
            expected_args.append(f"--ignore={','.join(expected_ignored)}")

        expected_args.extend(extra_args)
        expected_args.append(str(mock_path))

        mock_execute.assert_called_with(expected_args, verbose=mock_verbose)


def test_main(mocker):
    """Test houdini_package_runner.runners.flake8.runner.main."""
    mock_parsed = mocker.MagicMock(spec=argparse.Namespace)
    mock_unknown = mocker.MagicMock(spec=list)

    mock_parser = mocker.MagicMock(spec=argparse.ArgumentParser)
    mock_parser.parse_known_args.return_value = (mock_parsed, mock_unknown)

    mock_discoverer = mocker.MagicMock(spec=BaseItemDiscoverer)
    mock_init = mocker.patch(
        "houdini_package_runner.runners.flake8.runner.package.init_standard_package_discoverer",
        return_value=mock_discoverer,
    )

    mock_runner = mocker.MagicMock(
        spec=houdini_package_runner.runners.flake8.runner.Flake8Runner
    )

    mock_runner_init = mocker.patch(
        "houdini_package_runner.runners.flake8.runner.Flake8Runner",
        return_value=mock_runner,
    )
    mock_runner_init.build_parser.return_value = mock_parser

    result = houdini_package_runner.runners.flake8.runner.main()
    assert result == mock_runner.run.return_value

    mock_init.assert_called_with(mock_parsed)

    mock_runner_init.assert_called_with(mock_discoverer)
    mock_runner.init_args_options.assert_called_with(mock_parsed, mock_unknown)
    mock_runner.run.assert_called()
