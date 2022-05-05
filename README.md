[![PyPI version](https://img.shields.io/pypi/v/houdini_package_runner)](https://pypi.org/pypi/houdini_package_runner)
[![Tests](https://github.com/captainhammy/houdini_package_runner/actions/workflows/tests.yml/badge.svg)](https://github.com/captainhammy/houdini_package_runner/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/captainhammy/houdini_package_runner/branch/main/graph/badge.svg?token=H9YJQIAKZX)](https://codecov.io/gh/captainhammy/houdini_package_runner)

The **houdini_package_runner** project aims to provide an extensible API and set of tools for analyzing and acting upon
files in a Houdini package.

The current tools are all geared towards Python compatibility and styling.

Supported file types include:
- Python files and packages
- Python code/context sections inside Houdini XML type files
  - Menus (MainMenu*.xml, ParmMenu.xml, etc)
  - Python panels
  - Shelf tools
- Digital Assets (binary or expanded asset folders)
  - Python code sections (PythonModule, OnCreated, etc)
  - Python code inside DialogScript definition
    - Callbacks
    - Default parameter expressions
    - Menu scripts
  - Included shelf tools

Currently, the runner tools only function **outside** of Houdini on disk files.

The following read-only tool runners are provided:
- pylint - Perform [pylint](https://pypi.org/project/pylint/) analysis on Python code
- flake8 - Perform [flake8](https://pypi.org/project/flake8/) analysis on Python code

The following tool runner which can modify files are provided:
- black - Perform [black](https://pypi.org/project/black/) formatting on Python code
- isort - Use [isort](https://pypi.org/project/isort) to sort Python imports
- modernize - Use [python-modernize](https://pypi.org/project/modernize) for support Python 2 to 3 conversion.

NOTES:
- In order for the above runner tools to work you'll need to have them installed and available via commandline
- Operations on binary digital asset files (.otl, .hda) requires that Houdini's provided **hotl** command be available to run.
