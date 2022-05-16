"""Test the houdini_package_runner.config module."""

# =============================================================================
# IMPORTS
# =============================================================================

# Standard Library
import importlib.resources
import os
import pathlib

# Third Party
import pytest
import toml

# Houdini Package Runner
import houdini_package_runner.config
import houdini_package_runner.items.base

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def init_base_config(mocker):
    """Initialize a dummy BaseRunnerConfig for testing."""
    mocker.patch.multiple(
        houdini_package_runner.config.BaseRunnerConfig,
        __abstractmethods__=set(),
        __init__=lambda x, y: None,
    )

    def _create():
        return houdini_package_runner.config.BaseRunnerConfig(None)

    return _create


@pytest.fixture
def init_package_config(mocker):
    """Initialize a dummy PackageRunnerConfig for testing."""
    mocker.patch.multiple(
        houdini_package_runner.config.BaseRunnerConfig,
        __init__=lambda x, y: None,
    )

    def _create():
        return houdini_package_runner.config.PackageRunnerConfig(None)

    return _create


# =============================================================================
# TESTS
# =============================================================================


class TestBaseRunnerConfig:
    """Test houdini_package_runner.config.BaseRunnerConfig."""

    def test___init__(self, mocker, remove_abstract_methods):
        """Test object initialization."""
        remove_abstract_methods(houdini_package_runner.config.BaseRunnerConfig)

        mock_load = mocker.patch(
            "houdini_package_runner.config.BaseRunnerConfig.load_config"
        )

        mock_name = mocker.MagicMock(spec=str)

        inst = houdini_package_runner.config.BaseRunnerConfig(mock_name)

        assert inst._runner_name == mock_name
        assert inst._data == mock_load.return_value

    # Properties

    def test_data(self, mocker, init_base_config):
        """Test BaseRunnerConfig.data"""
        mock_data = mocker.MagicMock(spec=dict)

        inst = init_base_config()
        inst._data = mock_data

        assert inst.data == mock_data

        with pytest.raises(AttributeError):
            inst.data = {}

    def test_runner_name(self, mocker, init_base_config):
        """Test BaseRunnerConfig.runner_name"""
        mock_name = mocker.MagicMock(spec=str)

        inst = init_base_config()
        inst._runner_name = mock_name

        assert inst.runner_name == mock_name

        with pytest.raises(AttributeError):
            inst.runner_name = None


class TestPackageRunnerConfig:
    """Test houdini_package_runner.config.PackageRunnerConfig."""

    def test__get_file_config_data(self, mocker, shared_datadir, init_package_config):
        """Test PackageRunnerConfig._get_file_config_data"""
        config_file = shared_datadir / "get_file_config_data.toml"

        with config_file.open() as handle:
            data = toml.load(handle)

        file_path = pathlib.Path("/foo/OnCreated.py")

        inst = init_package_config()
        inst._data = data

        result = inst._get_file_config_data(file_path, "to_ignore")

        assert result == ["W292"]

    @pytest.mark.parametrize("test_item", (True, False))
    def test__get_item_config_data(
        self, mocker, shared_datadir, init_package_config, test_item
    ):
        """Test PackageRunnerConfig._get_item_config_data"""
        config_file = shared_datadir / "get_item_config_data.toml"

        with config_file.open() as handle:
            data = toml.load(handle)

        mock_build = mocker.patch(
            "houdini_package_runner.config.build_config_item_list",
            return_value=("XMLBase", "Foo", "BaseItem"),
        )

        mock_item = mocker.MagicMock(spec=houdini_package_runner.items.base.BaseItem)
        mock_item.is_test_item = test_item

        inst = init_package_config()
        inst._data = data

        result = inst._get_item_config_data(mock_item, "to_ignore")

        expected = ["W292", "A123"]

        if test_item:
            expected.append("T789")

        assert result == expected

        mock_build.assert_called_with(mock_item)

    def test_get_config_data(self, mocker, init_package_config):
        """Test PackageRunnerConfig.get_config_data"""
        mock_key = mocker.MagicMock(spec=str)
        mock_item = mocker.MagicMock(spec=houdini_package_runner.items.base.BaseItem)
        mock_path = mocker.MagicMock(spec=pathlib.Path)

        mock_get_item_data = mocker.patch.object(
            houdini_package_runner.config.PackageRunnerConfig,
            "_get_item_config_data",
            return_value=["item", "result"],
        )
        mock_get_file_data = mocker.patch.object(
            houdini_package_runner.config.PackageRunnerConfig,
            "_get_file_config_data",
            return_value=["file", "result"],
        )

        inst = init_package_config()

        result = inst.get_config_data(mock_key, mock_item, mock_path)

        assert result == ["item", "result", "file", "result"]

        mock_get_item_data.assert_called_with(mock_item, mock_key)
        mock_get_file_data.assert_called_with(mock_path, mock_key)

    def test_load_config(self, mocker, init_package_config):
        """Test PackageRunnerConfig.load_config"""
        mock_load = mocker.patch(
            "houdini_package_runner.config._load_default_runner_config"
        )
        mock_name = mocker.MagicMock(spec=str)

        inst = init_package_config()
        inst._runner_name = mock_name

        result = inst.load_config()

        assert result == mock_load.return_value

        mock_load.assert_called_with(mock_name)


@pytest.mark.parametrize("config_path_set", (True, False))
def test__find_config_files(mocker, config_path_set):
    """Test houdini_package_runner.config._find_config_files."""
    env_dict = {}

    if config_path_set:
        env_dict["HOUDINI_PACKAGE_RUNNER_CONFIG_PATH"] = os.pathsep.join(
            ["path1", "path2", "path3"]
        )
        mocker.patch("os.path.exists", side_effect=(True, False, True))

    mocker.patch.dict(os.environ, env_dict, clear=True)

    result = houdini_package_runner.config._find_config_files()

    if config_path_set:
        assert result == [pathlib.Path("path1"), pathlib.Path("path3")]

    else:
        with importlib.resources.path("houdini_package_runner", "runners.toml") as path:
            assert result == [path]


def test__load_default_runner_config(mocker, shared_datadir):
    """Test houdini_package_runner.config._load_default_runner_config."""
    test_data_path = shared_datadir / "test_load_runner_config"

    mocker.patch(
        "houdini_package_runner.config._find_config_files",
        return_value=[test_data_path / "config1.toml", test_data_path / "config2.toml"],
    )

    expected_path = test_data_path / "expected.toml"

    with expected_path.open("r") as handle:
        expected_data = toml.load(handle)

    result = houdini_package_runner.config._load_default_runner_config("runner_name")

    assert result == expected_data.get("runner_name")

    result = houdini_package_runner.config._load_default_runner_config("none")

    assert result == {}


def test_build_config_item_list():
    """Test houdini_package_runner.config.build_config_item_list.

    This will also test the recursive function __get_base_classes.

    """

    class A:
        """Test base class."""

    class B(A):
        """Another class"""

    class C(B):
        """Child class"""

    inst = C()

    result = houdini_package_runner.config.build_config_item_list(inst)

    assert result == ("C", "B", "A")
