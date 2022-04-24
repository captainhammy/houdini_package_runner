"""Test the houdini_package_runner.runners.isort.runner module."""

# =============================================================================
# IMPORTS
# =============================================================================

# Standard Library
import argparse
import configparser
import os
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
import houdini_package_runner.runners.isort.runner
from houdini_package_runner.discoverers.base import BaseItemDiscoverer


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def init_runner(mocker):
    """Initialize a dummy IsortRunner for testing."""
    mocker.patch.multiple(
        houdini_package_runner.runners.isort.runner.IsortRunner,
        __init__=lambda x, y: None,
    )

    def _create():
        return houdini_package_runner.runners.isort.runner.IsortRunner(None)

    return _create


# =============================================================================
# TESTS
# =============================================================================


class TestIsortRunner:
    """Test houdini_package_runner.runners.isort.runner.IsortRunner."""

    def test___init__(self, mocker):
        """Test object initialization."""
        mock_discoverer = mocker.MagicMock(spec=BaseItemDiscoverer)

        mock_super_init = mocker.patch.object(
            houdini_package_runner.runners.isort.runner.HoudiniPackageRunner, "__init__"
        )

        inst = houdini_package_runner.runners.isort.runner.IsortRunner(mock_discoverer)

        assert inst._extra_args == []

        mock_super_init.assert_called_with(mock_discoverer, write_back=True)

    # Non-Public Methods

    def test__generate_config(self, mocker, init_runner):
        """Test IsortRunner._generate_config."""
        mock_namespace = mocker.MagicMock(spec=argparse.Namespace)

        mock_load = mocker.patch(
            "houdini_package_runner.runners.isort.runner._load_template_config"
        )
        mock_save = mocker.patch(
            "houdini_package_runner.runners.isort.runner._save_template_config"
        )

        mock_temp_dir = mocker.MagicMock(spec=pathlib.Path)

        mock_process = mocker.patch.object(
            houdini_package_runner.runners.isort.runner.IsortRunner, "_process_config"
        )

        mocker.patch.object(
            houdini_package_runner.runners.isort.runner.IsortRunner,
            "temp_dir",
            mock_temp_dir,
        )

        inst = init_runner()

        result = inst._generate_config(mock_namespace)

        assert result == mock_save.return_value

        mock_process.assert_called_with(mock_load.return_value, mock_namespace)
        mock_save.assert_called_with(mock_load.return_value, mock_temp_dir)

    @pytest.mark.parametrize(
        "namespace_packages, python_root_exists",
        (
            (True, True),
            (False, None),
            (False, True),
            (False, False),
        ),
    )
    def test__process_config(
        self, mocker, init_runner, namespace_packages, python_root_exists
    ):
        """Test IsortRunner._process_config."""
        settings = {}
        config = {"settings": settings}

        mock_namespace = mocker.MagicMock(spec=argparse.Namespace)
        mock_namespace.package_names = (
            "first_party1,first_party2" if namespace_packages else None
        )
        mock_namespace.python_root = (
            "python" if python_root_exists is not None else None
        )
        mock_namespace.hfs_path = "$TEMP/houdini19.5"

        mock_discoverer_path = mocker.MagicMock(spec=pathlib.Path)

        mock_discoverer = mocker.MagicMock(spec=BaseItemDiscoverer)
        mock_discoverer.path = mock_discoverer_path
        mocker.patch.object(
            houdini_package_runner.runners.isort.runner.IsortRunner,
            "discoverer",
            mock_discoverer,
        )

        mock_discoverer_path.__truediv__.return_value.exists.return_value = (
            python_root_exists
        )

        mock_find_hfs = mocker.patch(
            "houdini_package_runner.runners.isort.runner._find_known_houdini",
            return_value=["hou", "toolutils"],
        )
        mock_find_python = mocker.patch(
            "houdini_package_runner.runners.isort.runner._find_python_packages_from_path",
            return_value="found_first_party1,found_first_party2",
        )

        inst = init_runner()

        inst._process_config(config, mock_namespace)

        if namespace_packages:
            assert settings["known_first_party"] == mock_namespace.package_names
            assert settings["import_heading_firstparty"] == "First Party1"

        else:
            if python_root_exists:
                assert (
                    settings["known_first_party"]
                    == "found_first_party1,found_first_party2"
                )
                assert settings["import_heading_firstparty"] == "Found First Party1"

                mock_find_python.assert_called_with(mock_discoverer_path / "python")

            else:
                mock_find_python.assert_not_called()
                assert "known_first_party" not in settings

        assert settings["known_houdini"] == "hou,toolutils"

        mock_find_hfs.assert_called_with(
            pathlib.Path(os.path.expandvars("$TEMP/houdini19.5"))
        )

    # Properties

    def test_config_file(self, mocker, init_runner):
        """Test IsortRunner.config_file."""
        mock_config = mocker.MagicMock(spec=str)

        inst = init_runner()
        inst._config_file = mock_config

        assert inst.config_file == mock_config

        inst._config_file = None
        inst.config_file = mock_config
        assert inst._config_file == mock_config

    def test_extra_args(self, mocker, init_runner):
        """Test IsortRunner.extra_args."""
        mock_args = mocker.MagicMock(spec=list)

        inst = init_runner()
        inst._extra_args = mock_args

        assert inst.extra_args == mock_args

        with pytest.raises(AttributeError):
            inst.extra_args = []

    # Methods

    @pytest.mark.parametrize("pass_parser", (True, False))
    def test_build_parser(self, mocker, pass_parser):
        """Test IsortRunner.build_parser."""
        mock_parser = mocker.MagicMock(spec=argparse.ArgumentParser)

        mock_build = mocker.patch(
            "houdini_package_runner.parser.build_common_parser",
            return_value=mock_parser,
        )

        if pass_parser:
            result = (
                houdini_package_runner.runners.isort.runner.IsortRunner.build_parser(
                    parser=mock_parser
                )
            )

            mock_build.assert_not_called()

        else:
            result = (
                houdini_package_runner.runners.isort.runner.IsortRunner.build_parser()
            )

            mock_build.assert_called()

        assert result == mock_parser

        result.add_argument.assert_has_calls(
            [
                mocker.call(
                    "--config-file",
                    action="store",
                    default=".isort.cfg",
                    help="Optional config file to pass to isort commands",
                ),
                mocker.call(
                    "--hfs-path",
                    action="store",
                    default="$HFS",
                    help="Path to a Houdini install directory for known Houdini modules",
                ),
                mocker.call(
                    "--package-names",
                    action="store",
                    help="Known first party package names",
                ),
            ]
        )

    @pytest.mark.parametrize(
        "namespace_config_exists",
        (None, True, False),
    )
    def test_init_args_options(self, mocker, init_runner, namespace_config_exists):
        """Test IsortRunner.init_args_options."""
        mock_namespace = mocker.MagicMock(spec=argparse.Namespace)
        mock_namespace.config_file = None

        mock_discoverer_path = mocker.MagicMock(spec=pathlib.Path)

        mock_discoverer = mocker.MagicMock(spec=BaseItemDiscoverer)
        mock_discoverer.path = mock_discoverer_path
        mocker.patch.object(
            houdini_package_runner.runners.isort.runner.IsortRunner,
            "discoverer",
            mock_discoverer,
        )

        mock_config_file = mocker.MagicMock(spec=str)

        if namespace_config_exists is not None:
            mock_namespace.config_file = mock_config_file
            mock_discoverer.path.__truediv__.return_value.exists.return_value = (
                namespace_config_exists
            )

        mock_extra_args = mocker.MagicMock(spec=list)

        mock_super_init = mocker.patch.object(
            houdini_package_runner.runners.isort.runner.HoudiniPackageRunner,
            "init_args_options",
        )

        mock_generate = mocker.patch.object(
            houdini_package_runner.runners.isort.runner.IsortRunner, "_generate_config"
        )

        inst = init_runner()
        inst._config_file = None

        inst.init_args_options(mock_namespace, mock_extra_args)

        mock_super_init.assert_called_with(mock_namespace, mock_extra_args)

        assert inst._extra_args == mock_extra_args

        if namespace_config_exists is not None:
            mock_discoverer.path.__truediv__.assert_called_with(mock_config_file)

        if namespace_config_exists:
            assert inst.config_file == mock_discoverer.path.__truediv__.return_value

        else:
            assert inst.config_file == mock_generate.return_value

            mock_generate.assert_called_with(mock_namespace)

    @pytest.mark.parametrize(
        "has_config",
        (True, False),
    )
    def test_process_path(self, mocker, init_runner, has_config):
        """Test IsortRunner.process_path."""
        mock_path = mocker.MagicMock(spec=pathlib.Path)

        mock_item = mocker.MagicMock(
            spec=houdini_package_runner.items.filesystem.FileToProcess
        )

        mock_execute = mocker.patch(
            "houdini_package_runner.utils.execute_subprocess_command"
        )

        extra_args = ["--flag", "arg"]

        mocker.patch.object(
            houdini_package_runner.runners.isort.runner.IsortRunner,
            "extra_args",
            extra_args,
        )

        mock_config_path = mocker.MagicMock(spec=pathlib.Path)
        config_file = mock_config_path if has_config else None

        mocker.patch.object(
            houdini_package_runner.runners.isort.runner.IsortRunner,
            "config_file",
            config_file,
        )

        mock_verbose = mocker.MagicMock(spec=bool)

        inst = init_runner()
        inst._verbose = mock_verbose

        inst.process_path(mock_path, mock_item)

        expected_args = ["isort"]

        if has_config:
            expected_args.extend(["--sp", str(mock_config_path)])

        expected_args.extend(extra_args + [str(mock_path)])

        mock_execute.assert_called_with(expected_args, verbose=mock_verbose)


def test__find_known_houdini(shared_datadir):
    """Test houdini_package_runner.runners.isort.runner._find_known_houdini."""
    test_path = shared_datadir / "test__find_known_houdini"
    result = houdini_package_runner.runners.isort.runner._find_known_houdini(test_path)

    assert result == ["IFDframe", "hjson", "hou", "hutil"]


def test__find_python_modules(shared_datadir):
    """Test houdini_package_runner.runners.isort.runner._find_python_modules."""
    test_path = shared_datadir / "test__find_python_modules"

    result = houdini_package_runner.runners.isort.runner._find_python_modules(test_path)

    assert result == ["compiled_module", "python_file", "test_dir"]


@pytest.mark.parametrize("packages_found", (True, False))
def test__find_python_packages_from_path(shared_datadir, packages_found):
    """Test houdini_package_runner.runners.isort.runner._find_python_packages_from_path."""
    if packages_found:
        test_path = (
            shared_datadir / "test__find_python_packages_from_path" / "has_packages"
        )

    else:
        test_path = shared_datadir / "test__find_python_packages_from_path"

    result = (
        houdini_package_runner.runners.isort.runner._find_python_packages_from_path(
            test_path
        )
    )

    if packages_found:
        assert result == "test_other_package,test_package"

    else:
        assert result is None


def test__load_template_config(mocker):
    """Test houdini_package_runner.runners.isort.runner._load_template_config."""
    mock_config = mocker.patch(
        "houdini_package_runner.runners.isort.runner.ConfigParser"
    )

    result = houdini_package_runner.runners.isort.runner._load_template_config()

    assert result == mock_config.return_value

    mock_config.return_value.read.assert_called_with(
        pathlib.Path(houdini_package_runner.runners.isort.runner.__file__).parent
        / "isort.cfg"
    )


def test__save_template_config(mocker):
    """Test houdini_package_runner.runners.isort.runner._save_template_config."""
    mock_config = mocker.MagicMock(spec=configparser.ConfigParser)
    mock_temp_path = mocker.MagicMock(spec=pathlib.Path)

    mock_handle = mocker.mock_open()
    mocker.patch("builtins.open", mock_handle)

    result = houdini_package_runner.runners.isort.runner._save_template_config(
        mock_config, mock_temp_path
    )

    assert result == mock_temp_path / ".isort.cfg"

    mock_handle.assert_called_with(mock_temp_path / ".isort.cfg", "w", encoding="utf-8")

    mock_config.write.assert_called_with(mock_handle.return_value)
