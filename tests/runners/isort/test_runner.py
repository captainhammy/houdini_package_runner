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
import houdini_package_runner.config
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

    @pytest.mark.parametrize("pass_optional", (False, True))
    def test___init__(self, mocker, pass_optional):
        """Test object initialization."""
        mock_discoverer = mocker.MagicMock(spec=BaseItemDiscoverer)

        mock_super_init = mocker.patch.object(
            houdini_package_runner.runners.isort.runner.HoudiniPackageRunner, "__init__"
        )

        mock_config = (
            mocker.MagicMock(spec=houdini_package_runner.config.PackageRunnerConfig)
            if pass_optional
            else None
        )

        if pass_optional:
            houdini_package_runner.runners.isort.runner.IsortRunner(
                mock_discoverer, runner_config=mock_config
            )

        else:
            houdini_package_runner.runners.isort.runner.IsortRunner(mock_discoverer)

        mock_super_init.assert_called_with(
            mock_discoverer, write_back=True, runner_config=mock_config
        )

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

    def test__get_first_party_header(self, init_runner):
        """Test IsortRunner._get_first_party_header."""
        package_names = "first_party1,first_party2"

        inst = init_runner()

        result = inst._get_first_party_header(package_names)

        assert result == "First Party1"

    @pytest.mark.parametrize(
        "namespace_packages, python_root_exists",
        (
            (True, True),
            (False, None),
            (False, True),
            (False, False),
        ),
    )
    def test__get_first_party_packages(
        self, mocker, init_runner, namespace_packages, python_root_exists
    ):
        """Test IsortRunner._get_first_party_packages."""

        mock_namespace = mocker.MagicMock(spec=argparse.Namespace)
        mock_namespace.package_names = (
            "first_party1,first_party2" if namespace_packages else None
        )
        mock_namespace.python_root = (
            "python" if python_root_exists is not None else None
        )

        mock_find_python = mocker.patch(
            "houdini_package_runner.runners.isort.runner._find_python_packages_from_path",
            return_value="found_first_party1,found_first_party2",
        )

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

        inst = init_runner()

        result = inst._get_first_party_packages(mock_namespace)

        if namespace_packages:
            assert result == mock_namespace.package_names

        else:
            if python_root_exists:
                assert result == "found_first_party1,found_first_party2"
                mock_find_python.assert_called_with(mock_discoverer_path / "python")

            else:
                assert result is None
                mock_find_python.assert_not_called()

    def test__get_houdini_names(self, mocker, init_runner):
        """Test IsortRunner._get_houdini_names."""
        mock_namespace = mocker.MagicMock(spec=argparse.Namespace)
        mock_namespace.hfs_path = "$TEMP/houdini19.5"

        mock_find_hfs = mocker.patch(
            "houdini_package_runner.runners.isort.runner._find_known_houdini",
            return_value=["hou", "toolutils"],
        )

        inst = init_runner()

        result = inst._get_houdini_names(mock_namespace)

        assert result == "hou,toolutils"

        mock_find_hfs.assert_called_with(
            pathlib.Path(os.path.expandvars("$TEMP/houdini19.5"))
        )

    @pytest.mark.parametrize("first_party_packages_set", (True, False))
    def test__process_config(self, mocker, init_runner, first_party_packages_set):
        """Test IsortRunner._process_config."""
        settings = {}
        config = {"settings": settings}

        mock_namespace = mocker.MagicMock(spec=argparse.Namespace)

        mock_find_houdini = mocker.patch(
            "houdini_package_runner.runners.isort.runner.IsortRunner._get_houdini_names",
        )
        mock_find_first = mocker.patch(
            "houdini_package_runner.runners.isort.runner.IsortRunner._get_first_party_packages",
        )

        mock_find_first.return_value = (
            "package1,package2" if first_party_packages_set else None
        )

        mock_find_header = mocker.patch(
            "houdini_package_runner.runners.isort.runner.IsortRunner._get_first_party_header",
        )

        inst = init_runner()

        inst._process_config(config, mock_namespace)

        assert settings["known_houdini"] == mock_find_houdini.return_value

        if first_party_packages_set:
            assert settings["known_first_party"] == mock_find_first.return_value
            assert (
                settings["import_heading_firstparty"] == mock_find_header.return_value
            )

        else:
            assert "known_first_party" not in settings

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

    def test_name(self, init_runner):
        """Test IsortRunner.name."""
        inst = init_runner()

        assert inst.name == "isort"

        with pytest.raises(AttributeError):
            inst.name = []

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
        "namespace_config_exists, pass_check",
        (
            (None, False),
            (True, True),
            (False, False),
        ),
    )
    def test_init_args_options(
        self, mocker, init_runner, namespace_config_exists, pass_check
    ):
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

        extra_args = ["--foo", "3"]

        if pass_check:
            extra_args.append("--check")

        mock_super_init = mocker.patch.object(
            houdini_package_runner.runners.isort.runner.HoudiniPackageRunner,
            "init_args_options",
        )

        mock_generate = mocker.patch.object(
            houdini_package_runner.runners.isort.runner.IsortRunner, "_generate_config"
        )

        inst = init_runner()
        inst._config_file = None
        inst._write_back = True

        inst.init_args_options(mock_namespace, extra_args)

        mock_super_init.assert_called_with(mock_namespace, extra_args)

        assert inst._extra_args == extra_args

        if namespace_config_exists is not None:
            mock_discoverer.path.__truediv__.assert_called_with(mock_config_file)

        if namespace_config_exists:
            assert inst.config_file == mock_discoverer.path.__truediv__.return_value

        else:
            assert inst.config_file == mock_generate.return_value

            mock_generate.assert_called_with(mock_namespace)

        if pass_check:
            assert not inst._write_back

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
    mock_open_text = mocker.patch("importlib.resources.open_text")

    mock_config = mocker.patch(
        "houdini_package_runner.runners.isort.runner.ConfigParser"
    )

    result = houdini_package_runner.runners.isort.runner._load_template_config()

    assert result == mock_config.return_value

    mock_config.return_value.read_file.assert_called_with(
        mock_open_text.return_value.__enter__.return_value
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


def test_main(mocker):
    """Test houdini_package_runner.runners.isort.runner.main."""
    mock_parsed = mocker.MagicMock(spec=argparse.Namespace)
    mock_unknown = mocker.MagicMock(spec=list)

    mock_parser = mocker.MagicMock(spec=argparse.ArgumentParser)
    mock_parser.parse_known_args.return_value = (mock_parsed, mock_unknown)

    mock_discoverer = mocker.MagicMock(spec=BaseItemDiscoverer)
    mock_init = mocker.patch(
        "houdini_package_runner.runners.flake8.runner.package.init_standard_package_discoverer",
        return_value=mock_discoverer,
    )

    mock_runner = mocker.MagicMock(
        spec=houdini_package_runner.runners.isort.runner.IsortRunner
    )

    mock_runner_init = mocker.patch(
        "houdini_package_runner.runners.isort.runner.IsortRunner",
        return_value=mock_runner,
    )
    mock_runner_init.build_parser.return_value = mock_parser

    result = houdini_package_runner.runners.isort.runner.main()
    assert result == mock_runner.run.return_value

    mock_init.assert_called_with(mock_parsed)

    mock_runner_init.assert_called_with(mock_discoverer)
    mock_runner.init_args_options.assert_called_with(mock_parsed, mock_unknown)
    mock_runner.run.assert_called()
