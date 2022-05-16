"""setup.py for houdini_package_runner."""
# Standard Library
from pathlib import Path

# Third Party
from setuptools import find_packages, setup

# Package meta-data.
NAME = "houdini_package_runner"
DESCRIPTION = "Tooling to analyze or perform actions on Python code in Houdini packages"
URL = "https://github.com/captainhammy/houdini_package_runner"
AUTHOR = "Graham Thompson"
AUTHOR_EMAIL = "captainhammy@gmail.com"
REQUIRES_PYTHON = ">=3.7.0"

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name=NAME,
    use_scm_version=True,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    package_dir={"": "src"},
    packages=find_packages(where="src", exclude=("tests",)),
    install_requires=[
        "black",
        "deepmerge",
        "flake8",
        "isort",
        "lxml",
        "modernize",
        "pylint",
        "pyparsing",
        "termcolor",
        "toml",
    ],
    extras_require={
        "test": [
            "pytest",
            "pytest-cov",
            "pytest-datadir",
            "pytest-mock",
            "pytest-subprocess",
            "tox",
        ]
    },
    entry_points={
        "console_scripts": [
            "houdini_package_black=houdini_package_runner.runners.black.runner:main",
            "houdini_package_flake8=houdini_package_runner.runners.flake8.runner:main",
            "houdini_package_isort=houdini_package_runner.runners.isort.runner:main",
            "houdini_package_modernize=houdini_package_runner.runners.modernize.runner:main",
            "houdini_package_pylint=houdini_package_runner.runners.pylint.runner:main",
        ],
    },
    include_package_data=True,
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: Unix",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Software Development :: Testing",
        "Topic :: Utilities",
    ],
)
