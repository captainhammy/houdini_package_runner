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


def execute_subprocess_command(command: List[str], verbose: bool = False) -> bool:
    """Execute a command in a subprocess, capturing and optionally outputting the output.

    :param command: A subprocess command list.
    :param verbose: Whether to capture output.
    :return: Whether the command finished successfully.

    """
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
            if proc.stdout is not None:
                for line in proc.stdout.readlines():
                    print(line.decode("utf-8"))

            if proc.stderr is not None:
                for line in proc.stderr.readlines():
                    print(line.decode("utf-8"))

        return return_code != 0
