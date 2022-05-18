"""This module contains utility functions."""

# =============================================================================
# IMPORTS
# =============================================================================

# Standard Library
import os
import subprocess
from typing import List

# =============================================================================
# FUNCTIONS
# =============================================================================


def add_or_append_to_flags(
    flags: List[str], key: str, values: List[str], separator: str = ","
):
    """Add or append to an existing arg flag with the separator.

    :param flags: The list of flags to modify.
    :param key: The new flag.
    :param values: The flag options.
    :param separator: The character used to join flag values.
    :return:

    """
    flag_str = separator.join(values)

    if key in flags:
        idx = flags.index(key) + 1
        flags[idx] = flags[idx] + separator + flag_str

    else:
        flags.extend((key, flag_str))


def execute_subprocess_command(command: List[str], verbose: bool = False) -> int:
    """Execute a command in a subprocess, capturing and optionally outputting the output.

    :param command: A subprocess command list.
    :param verbose: Whether to capture output.
    :return: The subprocess return code.

    """
    # If verbose mode is turned on then we don't want to capture the output.
    # so we'll set the output pipe to be None, otherwise we'll capture it.
    output_pipe = None if verbose else subprocess.PIPE

    env = os.environ.copy()

    # Remove PYTHONHOME from the env if it exists. This can cause problems for subprocesses
    # being executed from within Houdini.
    if "PYTHONHOME" in env:
        del env["PYTHONHOME"]

    with subprocess.Popen(
        command, stdout=output_pipe, stderr=output_pipe, env=env
    ) as proc:
        proc.wait()

        return_code = proc.returncode

        if return_code and not verbose:
            if proc.stdout is not None:  # pragma: no branch
                for line in proc.stdout.readlines():
                    print(line.decode("utf-8").rstrip())

            if proc.stderr is not None:  # pragma: no branch
                for line in proc.stderr.readlines():
                    print(line.decode("utf-8").rstrip())

        return return_code
