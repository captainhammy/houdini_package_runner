"""Runner related utilities."""

# Future
from __future__ import annotations

# Standard Library
from typing import TYPE_CHECKING, List, Optional

# Third Party
import termcolor

# Imports for type checking.
if TYPE_CHECKING:
    from houdini_package_runner.items.base import BaseItem


# =============================================================================
# FUNCTIONS
# =============================================================================


def print_runner_command(
    item: BaseItem, command: List[str], extra: Optional[str] = None
) -> None:
    """Print a runner item and command.

    The item will be output as cyan and the command as magenta, when possible.

    :param item: The item being processed.
    :param command: The list of command args being executed.
    :param extra: Optional value to prepend to the command output.
    :return:

    """
    if extra is None:
        extra = ""

    print(
        termcolor.colored(str(item), "cyan"),
        termcolor.colored(extra + " ".join(command), "magenta"),
    )
