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


@pytest.mark.parametrize(
    "extra_path, root_value, use_abs_path, raises",
    (
        (None, "houdini", True, False),
        (None, "houdini", False, False),
        (None, "other", False, True),
        ("houdini", None, False, False),
        (None, None, False, False),
    ),
)
def test__resolve_houdini_root(
    shared_datadir, extra_path, root_value, use_abs_path, raises
):
    """Test houdini_package_runner.parser._resolve_houdini_root."""
    test_root_path = shared_datadir / "resolve_houdini_root"

    abs_value = test_root_path / "houdini"

    if extra_path:
        test_root_path /= extra_path

    if use_abs_path:
        root_value = abs_value

    mock_namespace = argparse.Namespace()
    mock_namespace.houdini_root = root_value if root_value else None

    if raises:
        with pytest.raises(OSError):
            houdini_package_runner.parser._resolve_houdini_root(
                mock_namespace, test_root_path
            )

    else:
        result = houdini_package_runner.parser._resolve_houdini_root(
            mock_namespace, test_root_path
        )

        assert result == shared_datadir / "resolve_houdini_root" / "houdini"


@pytest.mark.parametrize("python_root", (None, "python", "other"))
def test__resolve_python_packages(shared_datadir, python_root):
    """Test houdini_package_runner.parser._resolve_python_packages."""
    test_root_path = shared_datadir / "resolve_python_packages"

    abs_value = test_root_path / "python"

    mock_namespace = argparse.Namespace()
    mock_namespace.python_root = python_root if python_root else None

    result = houdini_package_runner.parser._resolve_python_packages(
        mock_namespace, test_root_path
    )

    if python_root == "python":
        assert result == [abs_value]

    else:
        assert not result


@pytest.mark.parametrize(
    "extra_path, skip_tests",
    (
        (None, True),
        (None, False),
        ("foo", False),
    ),
)
def test__resolve_tests(shared_datadir, extra_path, skip_tests):
    """Test houdini_package_runner.parser._resolve_tests."""
    test_root_path = shared_datadir / "resolve_tests"

    if extra_path:
        test_root_path /= extra_path

    abs_value = test_root_path / "tests"

    mock_namespace = argparse.Namespace()
    mock_namespace.skip_tests = skip_tests

    result = houdini_package_runner.parser._resolve_tests(
        mock_namespace, test_root_path
    )

    if not skip_tests and not extra_path:
        assert result == [abs_value]

    else:
        assert not result


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
            default="otls,hda,toolbar,python_panels,pythonXlibs,scripts,soho,menus",
            help="A list of Houdini items to process",
        ),
        mocker.call(
            "--python-root",
            action="store",
            default="python",
            help="The root directory the package will be in",
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
            formatter_class=houdini_package_runner.parser._UltimateHelpFormatter,
        )

    assert mock_parser.add_argument.has_calls(calls)


@pytest.mark.parametrize("root_passed", (True, False))
def test_process_common_arg_settings(mocker, root_passed):
    """Test houdini_package_runner.parser.process_common_arg_settings."""
    namespace = argparse.Namespace()
    namespace.root = pathlib.Path("/some/root") if root_passed else None
    namespace.directories = ["directory1"]
    namespace.files = ["file1"]

    mock_python_dir = mocker.MagicMock(spec=pathlib.Path)
    mock_test_dir = mocker.MagicMock(spec=pathlib.Path)

    mock_houdini_root = mocker.patch(
        "houdini_package_runner.parser._resolve_houdini_root"
    )
    mocker.patch(
        "houdini_package_runner.parser._resolve_python_packages",
        return_value=[mock_python_dir],
    )
    mocker.patch(
        "houdini_package_runner.parser._resolve_tests", return_value=[mock_test_dir]
    )

    namespace.houdini_items = "otls,hda,python3.7libs"

    expected_root = namespace.root if root_passed else pathlib.Path.cwd()

    expected_extra = [
        expected_root / "directory1",
        mock_python_dir,
        mock_test_dir,
        expected_root / "file1",
    ]

    result = houdini_package_runner.parser.process_common_arg_settings(namespace)

    assert result == (
        expected_root,
        mock_houdini_root.return_value,
        expected_extra,
        namespace.houdini_items.split(","),
    )
