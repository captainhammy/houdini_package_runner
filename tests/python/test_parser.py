"""Test the houdini_package_runner.parser module."""

# =============================================================================
# IMPORTS
# =============================================================================

# Standard Library
import argparse
import pathlib

# Third Party
import pytest

# Houdini Package Runner
import houdini_package_runner.parser

# =============================================================================
# TESTS
# =============================================================================


@pytest.mark.parametrize("pass_args", (True, False))
def test_build_common_parser(mocker, pass_args):
    """Test houdini_package_runner.parser.build_common_parser."""
    # Store a reference to the parser class, so we can compare to it later on after
    # we do all sorts of mocking and patching.
    argparse_type = argparse.ArgumentParser

    mock_parser = mocker.MagicMock(spec=argparse.ArgumentParser)
    mock_init_parser = mocker.patch("argparse.ArgumentParser", return_value=mock_parser)

    if pass_args:
        result = houdini_package_runner.parser.build_common_parser(
            prog="program name", usage="usage", description="description"
        )
    else:
        result = houdini_package_runner.parser.build_common_parser()

    assert isinstance(result, argparse_type)

    calls = [
        mocker.call(
            "--add-dir",
            action="append",
            dest="directories",
            default=[],
            help="Add a directory to be processed",
        ),
        mocker.call(
            "--add-file",
            action="append",
            dest="files",
            default=[],
            help="Add a file to be processed",
        ),
        mocker.call(
            "--houdini-items",
            action="store",
            default="otls,toolbar,python_panels,python2.7libs,python3.7libs,scripts,soho,menus",
            help="A list of Houdini items to lint",
        ),
        mocker.call(
            "--python-root",
            action="store",
            default="python",
            help="The root directory the package will be in",
        ),
        mocker.call(
            "--skip-python",
            action="store_true",
            help="Skip processing of files under the python root.",
        ),
        mocker.call(
            "--root",
            action="store",
            help="Optional root directory to look for things from.  By default uses the cwd",
        ),
        mocker.call("--verbose", action="store_true", help="Engage verbose output."),
        mocker.call("--hotl-command", action="store", default="hotl"),
        mocker.call(
            "--skip-tests",
            action="store_true",
            help="Skip processing of files under {root}/tests.",
        ),
    ]

    if pass_args:
        mock_init_parser.assert_called_with(
            prog="program name",
            usage="usage",
            description="description",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )

    assert mock_parser.add_argument.has_calls(calls)


@pytest.mark.parametrize(
    "root_passed, has_py_root, python_exists, skip_python, skip_tests, tests_exists",
    (
        (True, False, False, False, False, True),
        (True, False, False, False, False, False),
        (True, True, True, False, True, True),
        (False, True, False, False, True, True),
        (False, True, True, True, True, True),
    ),
)
def test_process_common_arg_settings(
    mocker,
    root_passed,
    has_py_root,
    python_exists,
    skip_python,
    skip_tests,
    tests_exists,
):
    """Test houdini_package_runner.parser.process_common_arg_settings."""
    namespace = argparse.Namespace()
    namespace.root = pathlib.Path("/some/root") if root_passed else None
    namespace.directories = ["directory1"]
    namespace.python_root = "python" if has_py_root else None
    namespace.skip_python = skip_python
    namespace.skip_tests = skip_tests
    namespace.files = ["file1"]

    dir_exists = [tests_exists]

    if not skip_python and has_py_root:
        dir_exists.insert(0, python_exists)

    mocker.patch.object(pathlib.Path, "is_dir", side_effect=dir_exists)

    namespace.houdini_items = "otls,hda,python3.7libs"

    result = houdini_package_runner.parser.process_common_arg_settings(namespace)

    expected_root = pathlib.Path("/some/root") if root_passed else pathlib.Path.cwd()

    expected_dirs = [expected_root / "directory1"]

    if has_py_root and not skip_python and python_exists:
        expected_dirs.append(expected_root / "python")

    if not skip_tests and tests_exists:
        expected_dirs.append(expected_root / "tests")

    assert result[0] == expected_root

    assert result[1] == expected_dirs
    assert result[2] == [expected_root / "file1"]

    assert result[-1] == ["otls", "hda", "python3.7libs"]
