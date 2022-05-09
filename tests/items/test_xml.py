"""Test the houdini_package_runner.items.digital_asset module."""

# =============================================================================
# IMPORTS
# =============================================================================

# Standard Library
import pathlib

# Third Party
import pytest
from lxml import etree

# Houdini Package Runner
import houdini_package_runner.items.base
import houdini_package_runner.items.filesystem
import houdini_package_runner.items.xml
import houdini_package_runner.runners.base

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def init_base(mocker):
    """Initialize a dummy XMLBase for testing."""
    mocker.patch.multiple(
        houdini_package_runner.items.xml.XMLBase,
        __abstractmethods__=set(),
        __init__=lambda x, y, z, u: None,
    )

    def _create():
        return houdini_package_runner.items.xml.XMLBase(None, None, None)

    return _create


@pytest.fixture
def init_menu(mocker):
    """Initialize a dummy MenuFile for testing."""
    mocker.patch.multiple(
        houdini_package_runner.items.xml.MenuFile,
        __init__=lambda x, y, z, u: None,
    )

    def _create():
        return houdini_package_runner.items.xml.MenuFile(None, None, None)

    return _create


@pytest.fixture
def init_panel(mocker):
    """Initialize a dummy PythonPanelFile for testing."""
    mocker.patch.multiple(
        houdini_package_runner.items.xml.PythonPanelFile,
        __init__=lambda x, y, z, u: None,
    )

    def _create():
        return houdini_package_runner.items.xml.PythonPanelFile(None, None, None)

    return _create


@pytest.fixture
def init_shelf(mocker):
    """Initialize a dummy ShelfFile for testing."""
    mocker.patch.multiple(
        houdini_package_runner.items.xml.ShelfFile,
        __init__=lambda x, y, z, u, v: None,
    )

    def _create():
        return houdini_package_runner.items.xml.ShelfFile(None, None, None, None)

    return _create


# =============================================================================
# TESTS
# =============================================================================


class TestXMLBase:
    """Test houdini_package_runner.items.xml.XMLBase."""

    @pytest.mark.parametrize("default_args", (False, True))
    def test___init__(self, mocker, remove_abstract_methods, default_args):
        """Test object initialization."""
        remove_abstract_methods(houdini_package_runner.items.xml.XMLBase)

        mock_path = mocker.MagicMock(spec=pathlib.Path)
        mock_write_back = mocker.MagicMock(spec=bool)
        mock_display_name = mocker.MagicMock(spec=str)

        if default_args:
            inst = houdini_package_runner.items.xml.XMLBase(mock_path)

            assert not inst.write_back
            assert inst.display_name is None

        else:
            inst = houdini_package_runner.items.xml.XMLBase(
                mock_path, write_back=mock_write_back, display_name=mock_display_name
            )

            assert inst.write_back == mock_write_back
            assert inst.display_name == mock_display_name

        assert "hou" in inst.ignored_builtins
        assert "kwargs" in inst.ignored_builtins

    @pytest.mark.parametrize(
        "has_cdata, contents_changed",
        (
            (True, True),
            (True, False),
            (False, True),
            (False, False),
        ),
    )
    def test__handle_write_back(self, mocker, init_base, has_cdata, contents_changed):
        """Test XMLBase._handle_write_back."""
        tostring_result = (
            "something CDATA something" if has_cdata else "something something"
        )

        mock_tostring = mocker.patch(
            "houdini_package_runner.items.xml.etree.tostring",
            return_value=tostring_result,
        )
        mock_cdata = mocker.patch("houdini_package_runner.items.xml.etree.CDATA")

        mock_text = mocker.MagicMock(spec=str)
        mock_changed_text = mocker.MagicMock(spec=str)

        mock_cdata.return_value = mock_changed_text if contents_changed else mock_text

        mock_section = mocker.MagicMock()
        mock_section.text = mock_text

        mock_temp_path = mocker.MagicMock(spec=pathlib.Path)

        mock_handle = mocker.mock_open()
        mock_handle.return_value.read.return_value = (
            mock_changed_text if contents_changed else mock_text
        )
        mock_temp_path.open = mock_handle

        inst = init_base()
        inst._contents_changed = False

        inst._handle_write_back(mock_section, mock_temp_path)

        mock_tostring.assert_called_with(mock_section, encoding="unicode")

        if contents_changed:
            assert inst.contents_changed

            if has_cdata:
                assert mock_section.text == etree.CDATA(mock_changed_text)

            else:
                assert mock_section.text == mock_changed_text

        else:
            if has_cdata:
                assert mock_section.text == etree.CDATA(mock_text)

            else:
                assert mock_section.text == mock_text

    @pytest.mark.parametrize("write_back", (True, False))
    def test__process_code_section(self, mocker, init_base, write_back):
        """Test XMLBase._process_code_section."""
        mock_text = mocker.MagicMock(spec=str)

        mock_section = mocker.MagicMock()
        mock_section.text = mock_text

        mock_base_name = mocker.MagicMock(spec=str)

        mock_handle = mocker.mock_open()

        mock_temp_path = mocker.MagicMock(spec=pathlib.Path)
        mock_temp_path.open = mock_handle

        mock_runner = mocker.MagicMock(
            spec=houdini_package_runner.runners.base.HoudiniPackageRunner
        )
        mock_runner.temp_dir.__truediv__.return_value = mock_temp_path

        mock_handle_write_back = mocker.patch.object(
            houdini_package_runner.items.xml.XMLBase, "_handle_write_back"
        )

        inst = init_base()
        inst.write_back = write_back

        result = inst._process_code_section(mock_section, mock_runner, mock_base_name)

        assert result == mock_runner.process_path.return_value

        mock_runner.temp_dir.__truediv__.assert_called_with(f"{mock_base_name}.py")

        mock_temp_path.open.assert_called_with("w")
        mock_handle.return_value.write.assert_called_with(str(mock_text))

        mock_runner.process_path.assert_called_with(mock_temp_path, inst)

        if write_back:
            mock_handle_write_back.assert_called_with(mock_section, mock_temp_path)

        else:
            mock_handle_write_back.assert_not_called()

    @pytest.mark.parametrize(
        "write_back, contents_changed, return_codes, expected",
        (
            (True, True, (0, 0), 0),
            (True, False, (1, 0), 1),
            (False, True, (0, 1), 1),
            (False, False, (0, 0), 0),
        ),
    )
    def test_process(
        self, mocker, init_base, write_back, contents_changed, return_codes, expected
    ):
        """Test XMLBase.process."""
        mock_process = mocker.patch.object(
            houdini_package_runner.items.xml.XMLBase,
            "_process_code_section",
            side_effect=return_codes,
        )

        mock_section1 = mocker.MagicMock()
        mock_name1 = mocker.MagicMock()

        mock_section2 = mocker.MagicMock()
        mock_name2 = mocker.MagicMock()

        mock_get_items = mocker.patch.object(
            houdini_package_runner.items.xml.XMLBase, "_get_items_to_process"
        )
        mock_get_items.return_value = (
            (mock_section1, mock_name1),
            (mock_section2, mock_name2),
        )

        mock_root = mocker.MagicMock()

        mock_tree = mocker.MagicMock()
        mock_tree.getroot.return_value = mock_root

        mock_parser = mocker.patch("houdini_package_runner.items.xml.etree.XMLParser")
        mock_parse = mocker.patch(
            "houdini_package_runner.items.xml.etree.parse", return_value=mock_tree
        )

        mock_runner = mocker.MagicMock(
            spec=houdini_package_runner.runners.base.HoudiniPackageRunner
        )

        mock_path = mocker.MagicMock(spec=pathlib.Path)

        inst = init_base()
        inst._path = mock_path
        inst.write_back = write_back
        inst.contents_changed = contents_changed

        result = inst.process(mock_runner)

        assert result == expected

        mock_parser.assert_called_with(strip_cdata=False)
        mock_parse.assert_called_with(str(inst.path), mock_parser.return_value)
        mock_get_items.assert_called_with(mock_root)

        mock_process.assert_has_calls(
            (
                mocker.call(mock_section1, mock_runner, mock_name1),
                mocker.call(mock_section2, mock_runner, mock_name2),
            )
        )

        if write_back and contents_changed:
            mock_tree.write.assert_called_with(
                str(inst.path), encoding="utf-8", xml_declaration=True
            )

        else:
            mock_tree.write.assert_not_called()


class TestMenuFile:
    """Test houdini_package_runner.items.xml.MenuFile."""

    def test__get_items_to_process(self, shared_datadir, init_menu):
        """Test MenuFile._get_items_to_process."""
        test_path = shared_datadir / "test_menu__get_items_to_process.xml"
        root = _load_test_file(test_path)

        inst = init_menu()

        result = inst._get_items_to_process(root)

        assert len(result) == 4

        assert result[0][0].text == "promote code"
        assert result[0][1] == "promote_item"

        assert result[1][0].text == "item code"
        assert result[1][1] == "item_with_context"

        assert result[2][0].text == "context code"
        assert result[2][1] == "item_with_context.context"

        assert result[3][0].text == "missing context item code"
        assert result[3][1] == "item_with_context_missing_expressions"


class TestPythonPanelFile:
    """Test houdini_package_runner.items.xml.PythonPanelFile."""

    def test__get_items_to_process(self, shared_datadir, init_panel):
        """Test PythonPanelFile._get_items_to_process."""
        test_path = shared_datadir / "test_pypanel__get_items_to_process.xml"
        root = _load_test_file(test_path)

        inst = init_panel()

        result = inst._get_items_to_process(root)

        assert len(result) == 2

        assert result[0][0].text == "script code"
        assert result[0][1] == "test_panel"

        assert result[1][0].text == "more script code"
        assert result[1][1] == "test_other_panel"


class TestShelfFile:
    """Test houdini_package_runner.items.xml.ShelfFile."""

    @pytest.mark.parametrize("default_args", (False, True))
    def test___init__(self, mocker, default_args):
        """Test object initialization."""
        mock_path = mocker.MagicMock(spec=pathlib.Path)
        mock_write_back = mocker.MagicMock(spec=bool)
        mock_display_name = mocker.MagicMock(spec=str)
        mock_tool_name = mocker.MagicMock(spec=str)

        mock_super_init = mocker.patch.object(
            houdini_package_runner.items.xml.XMLBase, "__init__"
        )

        if default_args:
            inst = houdini_package_runner.items.xml.ShelfFile(mock_path)

            mock_super_init.assert_called_with(
                mock_path, write_back=False, display_name=None
            )

            assert inst._tool_name is None

        else:
            inst = houdini_package_runner.items.xml.ShelfFile(
                mock_path,
                write_back=mock_write_back,
                display_name=mock_display_name,
                tool_name=mock_tool_name,
            )

            mock_super_init.assert_called_with(
                mock_path, write_back=mock_write_back, display_name=mock_display_name
            )

            assert inst._tool_name == mock_tool_name

    @pytest.mark.parametrize("tool_name", (None, "com.houdinitoolbox::Sop/foo::1"))
    def test__get_items_to_process(self, shared_datadir, init_shelf, tool_name):
        """Test ShelfFile._get_items_to_process."""
        test_path = shared_datadir / "test_shelf__get_items_to_process.shelf"
        root = _load_test_file(test_path)

        inst = init_shelf()
        inst._tool_name = tool_name

        result = inst._get_items_to_process(root)

        assert len(result) == 2

        assert result[0][0].text == "shelf code"
        assert result[0][1] == "copy_items"

        assert result[1][0].text == "hda code"

        if tool_name:
            assert result[1][1] == "com.houdinitoolbox__Sop_foo__1_DEFAULT_TOOL"

        else:
            assert result[1][1] == "$HDA_DEFAULT_TOOL"


def _load_test_file(path: pathlib.Path) -> etree._Element:
    """Load a test xml file.

    :param path: The test file path.
    :return: The XML root.

    """
    parser = etree.XMLParser(strip_cdata=False)
    tree = etree.parse(str(path), parser)

    return tree.getroot()
