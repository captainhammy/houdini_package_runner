"""Test the houdini_package_runner.utils module."""

# =============================================================================
# IMPORTS
# =============================================================================

# Standard Library
import copy
import os

# Third Party
import pytest

# Houdini Package Runner
import houdini_package_runner.utils

# =============================================================================
# TESTS
# =============================================================================


@pytest.mark.parametrize(
    "flags, key, values, sep, expected",
    (
        ([], "--to-skip", ["foo", "bar"], None, ["--to-skip", "foo,bar"]),
        ([], "--to-skip", ["foo", "bar"], "_", ["--to-skip", "foo_bar"]),
        (
            ["--thing"],
            "--to-skip",
            ["foo", "bar"],
            None,
            ["--thing", "--to-skip", "foo,bar"],
        ),
        (
            ["--to-skip", "baz", "--thing"],
            "--to-skip",
            ["foo", "bar"],
            None,
            ["--to-skip", "baz,foo,bar", "--thing"],
        ),
    ),
)
def test_add_or_append_to_flags(flags, key, values, sep, expected):
    """Test houdini_package_runner.utils.add_or_append_to_flags"""
    test_flags = copy.copy(flags)

    if sep is not None:
        houdini_package_runner.utils.add_or_append_to_flags(
            test_flags, key, values, sep
        )

    else:
        houdini_package_runner.utils.add_or_append_to_flags(test_flags, key, values)

    assert test_flags == expected


@pytest.mark.parametrize(
    "verbose, has_pyhome, return_code",
    (
        (False, False, 0),
        (False, False, 1),
        (False, True, 0),
        (True, False, 0),
        (True, False, 1),
    ),
)
def test_execute_subprocess_command(mocker, fp, verbose, has_pyhome, return_code):
    """Test houdini_package_runner.utils.execute_subprocess_command."""
    stdout = "This is stdout\n" if return_code and not verbose else None
    stderr = "This is stderr\n" if return_code and not verbose else None

    mock_print = mocker.patch("builtins.print")

    # Make a copy of the env to use for passing to the test.
    dummy_env = os.environ.copy()

    # Remove PYTHONHOME in case it is set, so we can explicitly control whether it is
    # set or not.
    if "PYTHONHOME" in dummy_env:
        del dummy_env["PYTHONHOME"]

    if has_pyhome:
        dummy_env["PYTHONHOME"] = "/some/path"

    mocker.patch("os.environ.copy", return_value=dummy_env)

    cmd = ["hotl", "-t", "foobles", "barbles.otl"]

    fp.register(cmd, returncode=return_code, stdout=stdout, stderr=stderr)

    result = houdini_package_runner.utils.execute_subprocess_command(cmd, verbose)

    assert result == return_code

    # If we are testing with PYTHONHOME in the env, make sure it got removed.
    if has_pyhome:
        assert "PYTHONHOME" not in dummy_env

    if return_code and not verbose:
        mock_print.assert_has_calls(
            [
                mocker.call(stdout.rstrip()),
                mocker.call(stderr.rstrip()),
            ]
        )
