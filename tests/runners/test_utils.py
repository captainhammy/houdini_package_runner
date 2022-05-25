"""Test the houdini_package_runner.runners.utils module."""

# =============================================================================
# IMPORTS
# =============================================================================

# Third Party
import pytest

# Houdini Package Runner
import houdini_package_runner.items.base
import houdini_package_runner.runners.utils

# =============================================================================
# TESTS
# =============================================================================


@pytest.mark.parametrize(
    "command, extra, expected",
    (
        (["--foo", "--bar"], None, "--foo --bar"),
        (["--foo", "--bar"], "", "--foo --bar"),
        (["--foo", "--bar"], "extra --stuff ", "extra --stuff --foo --bar"),
    ),
)
def test_print_runner_command(mocker, command, extra, expected):
    """Test houdini_package_runner.utils.print_runner_command."""
    mock_print = mocker.patch("builtins.print")

    mock_colored = mocker.patch("termcolor.colored")

    mock_item = mocker.MagicMock(spec=houdini_package_runner.items.base.BaseItem)

    if extra is not None:
        houdini_package_runner.runners.utils.print_runner_command(
            mock_item, command, extra=extra
        )

    else:
        houdini_package_runner.runners.utils.print_runner_command(mock_item, command)

    mock_print.assert_called_with(mock_colored.return_value, mock_colored.return_value)

    mock_colored.assert_has_calls(
        (
            mocker.call(str(mock_item), "cyan"),
            mocker.call(expected, "magenta"),
        )
    )
