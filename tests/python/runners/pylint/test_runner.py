"""Test the houdini_package_runner.runners.pylint.runner module."""

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
import houdini_package_runner.runners.pylint.runner
from houdini_package_runner.discoverers.base import BaseItemDiscoverer

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def init_runner(mocker):
    """Initialize a dummy PyLintRunner for testing."""
    mocker.patch.multiple(
        houdini_package_runner.runners.pylint.runner.PyLintRunner,
        __init__=lambda x, y: None,
    )

    def _create():
        return houdini_package_runner.runners.pylint.runner.PyLintRunner(None)

    return _create


# =============================================================================
# TESTS
# =============================================================================


class TestPyLintRunner:
    """Test houdini_package_runner.runners.pylint.runner.PyLintRunner."""

    def test___init__(self, mocker):
        """Test object initialization."""
        mock_discoverer = mocker.MagicMock(spec=BaseItemDiscoverer)

        mock_super_init = mocker.patch.object(
            houdini_package_runner.runners.pylint.runner.HoudiniPackageRunner,
            "__init__",
        )

        inst = houdini_package_runner.runners.pylint.runner.PyLintRunner(
            mock_discoverer
        )

        assert inst._disabled == []
        assert isinstance(inst._extra_args, list)
        assert not inst._extra_args

        mock_super_init.assert_called_with(mock_discoverer)

    # Properties

    def test_extra_args(self, mocker, init_runner):
        """Test PyLintRunner.extra_args."""
        mock_args = mocker.MagicMock(spec=list)

        inst = init_runner()
        inst._extra_args = mock_args

        assert inst.extra_args == mock_args

        with pytest.raises(AttributeError):
            inst.extra_args = []

    # Methods

    @pytest.mark.parametrize("pass_parser", (True, False))
    def test_build_parser(self, mocker, pass_parser):
        """Test PyLintRunner.build_parser."""
        mock_parser = mocker.MagicMock(spec=argparse.ArgumentParser)

        mock_build = mocker.patch(
            "houdini_package_runner.parser.build_common_parser",
            return_value=mock_parser,
        )

        if pass_parser:
            result = (
                houdini_package_runner.runners.pylint.runner.PyLintRunner.build_parser(
                    parser=mock_parser
                )
            )

            mock_build.assert_not_called()

        else:
            result = (
                houdini_package_runner.runners.pylint.runner.PyLintRunner.build_parser()
            )

            mock_build.assert_called()

        assert result == mock_parser

        result.add_argument.assert_has_calls(
            [
                mocker.call(
                    "--rcfile",
                    action="store",
                    help="Specify a configuration file",
                ),
                mocker.call("--disable", action="store", help="Tests to disable."),
            ]
        )

    @pytest.mark.parametrize("has_options_set", (True, False))
    def test_init_args_options(self, mocker, init_runner, has_options_set):
        """Test PyLintRunner.init_args_options."""
        mock_namespace = mocker.MagicMock()

        if has_options_set:
            mock_namespace.disable = "a,b"
            mock_namespace.rcfile = "thing.rc"
            extra_args = ["arg1", "arg2"]

        else:
            mock_namespace.disable = None
            mock_namespace.rcfile = None
            extra_args = []

        expected_extra_args = copy.copy(extra_args)

        if has_options_set:
            expected_extra_args.insert(0, f"--rcfile={mock_namespace.rcfile}")

        mock_super_init = mocker.patch.object(
            houdini_package_runner.runners.pylint.runner.HoudiniPackageRunner,
            "init_args_options",
        )

        inst = init_runner()
        inst._disabled = []
        inst._ignored = []
        inst._extra_args = []

        inst.init_args_options(mock_namespace, extra_args)

        mock_super_init.assert_called_with(mock_namespace, extra_args)

        assert inst._extra_args == extra_args

        if has_options_set:
            assert inst._disabled == ["a", "b"]

        else:
            assert inst._disabled == []

    @pytest.mark.parametrize(
        "has_disabled, item_type, has_builtins, verbose, test_item",
        (
            (
                True,
                houdini_package_runner.items.dialog_script.DialogScriptInternalItem,
                True,
                True,
                True,
            ),
            (False, houdini_package_runner.items.xml.MenuFile, False, False, False),
            (
                False,
                houdini_package_runner.items.filesystem.FileToProcess,
                False,
                False,
                False,
            ),
        ),
    )
    def test_process_path(
        self,
        mocker,
        init_runner,
        has_disabled,
        item_type,
        has_builtins,
        verbose,
        test_item,
    ):
        """Test PyLintRunner.process_path."""
        mock_io = mocker.patch("houdini_package_runner.runners.pylint.runner.StringIO")
        mock_run = mocker.patch("houdini_package_runner.runners.pylint.runner.lint.Run")
        mock_reporter = mocker.patch(
            "houdini_package_runner.runners.pylint.runner.ColorizedTextReporter"
        )

        mock_print = mocker.patch("builtins.print")
        mock_write = mocker.patch("sys.stdout.write")

        mock_colored = mocker.patch("termcolor.colored")

        mock_path = mocker.MagicMock(spec=pathlib.Path)

        mock_item = mocker.MagicMock(spec=item_type)

        mock_item.ignored_builtins = ["hou"] if has_builtins else []
        mock_item.is_test_item = test_item

        mock_add_flags = mocker.patch(
            "houdini_package_runner.utils.add_or_append_to_flags"
        )

        extra_args = ["--flag", "arg"]

        mocker.patch.object(
            houdini_package_runner.runners.pylint.runner.PyLintRunner,
            "extra_args",
            extra_args,
        )

        expected_disabled = []

        inst = init_runner()
        inst._disabled = []
        inst._verbose = verbose

        if has_disabled:
            inst._disabled = ["one-thing"]
            expected_disabled = inst._disabled

        inst.process_path(mock_path, mock_item)

        expected_args = [str(mock_path)]
        expected_args.extend(extra_args)

        if isinstance(mock_item, houdini_package_runner.items.xml.XMLBase):
            expected_disabled.extend(
                [
                    "invalid-name",
                    "missing-final-newline",
                    "missing-module-docstring",
                    "missing-docstring",
                    "return-outside-function",
                ]
            )

        elif isinstance(
            mock_item,
            houdini_package_runner.items.dialog_script.DialogScriptInternalItem,
        ):
            expected_disabled.extend(
                [
                    "invalid-name",
                    "missing-final-newline",
                    "missing-module-docstring",
                    "return-outside-function",
                ]
            )

        if test_item:
            expected_disabled.extend(
                [
                    "abstract-class-instantiated",
                    "no-self-use",
                    "protected-access",
                    "too-many-arguments",
                    "too-many-locals",
                    "cannot-enumerate-pytest-fixtures",
                ]
            )

        if has_builtins:
            # Only do assert_called() here as the command list will change and be inaccurate.
            mock_add_flags.assert_called()

        if expected_disabled:
            expected_args.append(f"--disable={','.join(expected_disabled)}")

        if verbose:
            mock_print.assert_has_calls(
                (
                    mocker.call(mock_colored.return_value, mock_colored.return_value),
                    mocker.call(),
                )
            )

            mock_colored.assert_has_calls(
                (
                    mocker.call(str(mock_item), "cyan"),
                    mocker.call(" ".join(expected_args[1:]), "magenta"),
                )
            )

        mock_run.assert_called_with(
            expected_args, reporter=mock_reporter.return_value, exit=False
        )

        mock_reporter.assert_called_with(mock_io.return_value)
        mock_write.assert_called_with(mock_io.return_value.getvalue.return_value)


def test_main(mocker):
    """Test houdini_package_runner.runners.black.runner.main."""
    mock_parsed = mocker.MagicMock(spec=argparse.Namespace)
    mock_unknown = mocker.MagicMock(spec=list)

    mock_parser = mocker.MagicMock(spec=argparse.ArgumentParser)
    mock_parser.parse_known_args.return_value = (mock_parsed, mock_unknown)

    mock_discoverer = mocker.MagicMock(spec=BaseItemDiscoverer)
    mock_init = mocker.patch(
        "houdini_package_runner.runners.pylint.runner.package.init_standard_discoverer",
        return_value=mock_discoverer,
    )

    mock_runner = mocker.MagicMock(
        spec=houdini_package_runner.runners.pylint.runner.PyLintRunner
    )

    mock_runner_init = mocker.patch(
        "houdini_package_runner.runners.pylint.runner.PyLintRunner",
        return_value=mock_runner,
    )
    mock_runner_init.build_parser.return_value = mock_parser

    houdini_package_runner.runners.pylint.runner.main()

    mock_init.assert_called_with(mock_parsed)

    mock_runner_init.assert_called_with(mock_discoverer)
    mock_runner.init_args_options.assert_called_with(mock_parsed, mock_unknown)
    mock_runner.run.assert_called()
