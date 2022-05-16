"""Test the houdini_package_runner.items.dialog_script module."""

# =============================================================================
# IMPORTS
# =============================================================================

# Standard Library
import pathlib

# Third Party
import pytest

# Houdini Package Runner
import houdini_package_runner.items.base
import houdini_package_runner.items.dialog_script
import houdini_package_runner.runners.base

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def init_item(mocker):
    """Initialize a dummy DialogScriptItem for testing."""
    mocker.patch.multiple(
        houdini_package_runner.items.dialog_script.DialogScriptItem,
        __init__=lambda x, y, z, u, v: None,
    )

    def _create():
        return houdini_package_runner.items.dialog_script.DialogScriptItem(
            None, None, None, None
        )

    return _create


@pytest.fixture
def init_internal_item(mocker):
    """Initialize a dummy DialogScriptInternalItem for testing."""
    mocker.patch.multiple(
        houdini_package_runner.items.dialog_script.DialogScriptInternalItem,
        __init__=lambda x, y, z, u, v, w: None,
    )

    def _create():
        return houdini_package_runner.items.dialog_script.DialogScriptInternalItem(
            None, None, None, None, None
        )

    return _create


@pytest.fixture
def init_menu_item(mocker):
    """Initialize a dummy DialogScriptMenuScriptItem for testing."""
    mocker.patch.multiple(
        houdini_package_runner.items.dialog_script.DialogScriptMenuScriptItem,
        __init__=lambda x, y, z, u, v, w: None,
    )

    def _create():
        return houdini_package_runner.items.dialog_script.DialogScriptMenuScriptItem(
            None, None, None, None, None
        )

    return _create


# =============================================================================
# TESTS
# =============================================================================


class TestDialogScriptItem:
    """Test houdini_package_runner.items.dialog_script.DialogScriptItem."""

    @pytest.mark.parametrize("pass_defaults", (True, False))
    def test___init__(self, mocker, pass_defaults):
        """Test object initialization."""
        mock_path = mocker.MagicMock(spec=pathlib.Path)
        mock_name = mocker.MagicMock(spec=str)
        mock_write_back = mocker.MagicMock(spec=bool)
        mock_source_file = mocker.MagicMock(spec=pathlib.Path)

        mock_contents = mocker.MagicMock(spec=str)

        mock_handle = mocker.mock_open()
        mock_handle.return_value.read.return_value = mock_contents

        mock_path.open = mock_handle

        mock_super_init = mocker.patch.object(
            houdini_package_runner.items.base.BaseFileItem, "__init__"
        )

        mocker.patch.object(
            houdini_package_runner.items.dialog_script.DialogScriptItem,
            "path",
            new_callable=mocker.PropertyMock(return_value=mock_path),
        )

        if pass_defaults:
            inst = houdini_package_runner.items.dialog_script.DialogScriptItem(
                mock_path, mock_name
            )
            mock_super_init.assert_called_with(mock_path, write_back=False)
            assert inst._source_file is None

        else:
            inst = houdini_package_runner.items.dialog_script.DialogScriptItem(
                mock_path,
                mock_name,
                write_back=mock_write_back,
                source_file=mock_source_file,
            )
            mock_super_init.assert_called_with(mock_path, write_back=mock_write_back)
            assert inst._source_file == mock_source_file

        assert inst._name == mock_name
        assert inst._ds_contents == mock_contents

        mock_handle.assert_called_with(encoding="utf-8")

    @pytest.mark.parametrize(
        "write_back, test_file",
        (
            (False, "test__gather_items.ds"),
            (True, "test__gather_items.ds"),
            (False, None),
        ),
    )
    def test__gather_items(
        self, mocker, shared_datadir, init_item, write_back, test_file
    ):
        """Test DialogScriptItem._gather_items"""
        if test_file is not None:
            with (shared_datadir / test_file).open() as handle:
                contents = handle.read()
        else:
            contents = ""

        mock_callbacks = [mocker.MagicMock(), mocker.MagicMock()]
        mock_expressions = [mocker.MagicMock()]
        mock_menus = [mocker.MagicMock(), mocker.MagicMock()]

        for item in tuple(mock_callbacks + mock_expressions + mock_menus):
            item.write_back = False

        mock_get_callbacks = mocker.patch(
            "houdini_package_runner.items.dialog_script._get_callback_items",
            return_value=mock_callbacks,
        )
        mock_get_expressions = mocker.patch(
            "houdini_package_runner.items.dialog_script._get_expression_items",
            return_value=mock_expressions,
        )
        mock_get_menus = mocker.patch(
            "houdini_package_runner.items.dialog_script._get_menu_items",
            return_value=mock_menus,
        )

        parm_value = 'parm {\n        name    "newparameter"\n        label   "Label"\n        type    float\n        default { [ "hou.pwd().path()[-1]" python ] }\n        range   { 0 10 }\n        parmtag { "script_callback" "" }\n        parmtag { "script_callback_language" "python" }\n    }'  # noqa: E501

        mock_name = mocker.MagicMock(spec=str)

        inst = init_item()
        inst._write_back = write_back
        inst._name = mock_name
        inst._ds_contents = contents

        result = inst._gather_items()

        if test_file:
            assert result == tuple(mock_callbacks + mock_expressions + mock_menus)

            mock_get_callbacks.assert_called_with(parm_value, 4, mock_name)
            mock_get_expressions.assert_called_with(parm_value, 4, mock_name)
            mock_get_menus.assert_called_with(parm_value, 4, mock_name)

            for item in result:
                assert item.write_back == write_back

        else:
            assert not result

    def test__handle_changed_contents(self, mocker, shared_datadir, init_item):
        """Test DialogScriptItem._handle_changed_contents"""
        output_path = shared_datadir / "_handle_changed_contents.ds"

        with (
            shared_datadir / "test__handle_changed_contents" / "original.ds"
        ).open() as handle:
            original_contents = handle.read()

        with (
            shared_datadir / "test__handle_changed_contents" / "expected.ds"
        ).open() as handle:
            expected_contents = handle.read()

        mock_item1 = mocker.MagicMock()
        mock_item1.start_offset = 51
        mock_item1.end_offset = 59
        mock_item1.post_processed_code = "DIFFERENT NEW"

        mock_item2 = mocker.MagicMock()
        mock_item2.start_offset = 11
        mock_item2.end_offset = 19
        mock_item2.post_processed_code = "NEW"

        items = [mock_item1, mock_item2]

        inst = init_item()
        inst._ds_contents = original_contents
        type(inst).path = mocker.PropertyMock(return_value=output_path)

        inst._handle_changed_contents(items)

        with output_path.open() as handle:
            output_contents = handle.read()

        assert items == [mock_item2, mock_item1]
        assert output_contents == expected_contents

    # Properties

    def test_name(self, mocker, init_item):
        """Test DialogScriptItem.name"""
        mock_name = mocker.MagicMock(spec=str)

        inst = init_item()
        inst._name = mock_name

        assert inst.name == mock_name

        with pytest.raises(AttributeError):
            inst.name = "some name"

    # Methods

    @pytest.mark.parametrize(
        "write_back, has_changed_contents, return_codes, expected",
        (
            (True, True, (0, 0), 0),
            (True, False, (1, 0), 1),
            (False, True, (0, 1), 1),
        ),
    )
    def test_process(
        self,
        mocker,
        init_item,
        write_back,
        has_changed_contents,
        return_codes,
        expected,
    ):
        """Test DialogScriptItem.process."""
        mock_runner = mocker.MagicMock(
            spec=houdini_package_runner.runners.base.HoudiniPackageRunner
        )

        mock_file1 = mocker.MagicMock()
        mock_file1.contents_changed = has_changed_contents
        mock_file1.process.return_value = return_codes[0]

        mock_file2 = mocker.MagicMock()
        mock_file2.contents_changed = False
        mock_file2.process.return_value = return_codes[1]

        mocker.patch.object(
            houdini_package_runner.items.dialog_script.DialogScriptItem,
            "_gather_items",
            return_value=[mock_file1, mock_file2],
        )
        mock_handle = mocker.patch.object(
            houdini_package_runner.items.dialog_script.DialogScriptItem,
            "_handle_changed_contents",
        )

        inst = init_item()
        inst._contents_changed = False
        inst._write_back = write_back

        result = inst.process(mock_runner)

        assert result == expected

        mock_file1.process.assert_called_with(mock_runner)
        mock_file2.process.assert_called_with(mock_runner)

        if write_back and has_changed_contents:
            mock_handle.assert_called_with([mock_file1])

            assert inst.contents_changed

        else:
            assert not inst.contents_changed


class TestDialogScriptInternalItem:
    """Test houdini_package_runner.items.dialog_script.DialogScriptInternalItem."""

    @pytest.mark.parametrize("pass_defaults", (True, False))
    def test___init__(self, mocker, pass_defaults):
        """Test object initialization."""
        mock_parm = mocker.MagicMock(spec=str)
        mock_code = mocker.MagicMock(spec=str)
        mock_start_offset = mocker.MagicMock(spec=int)
        mock_end_offset = mocker.MagicMock(spec=int)
        mock_display_name = mocker.MagicMock(spec=str)
        mock_write_back = mocker.MagicMock(spec=bool)

        mock_super_init = mocker.patch.object(
            houdini_package_runner.items.dialog_script.BaseItem, "__init__"
        )

        ignored = []

        mocker.patch.object(
            houdini_package_runner.items.dialog_script.DialogScriptInternalItem,
            "ignored_builtins",
            ignored,
        )

        parm_name_result = [["first", "second"], ["third"]]
        mock_search = mocker.patch(
            "houdini_package_runner.items.dialog_script._DS_NAME_EXPR_GRAMMAR.searchString"
        )
        mock_search.return_value = parm_name_result

        if pass_defaults:
            inst = houdini_package_runner.items.dialog_script.DialogScriptInternalItem(
                mock_parm,
                mock_code,
                mock_start_offset,
                mock_end_offset,
                mock_display_name,
            )

            mock_super_init.assert_called_with(write_back=False)

        else:
            inst = houdini_package_runner.items.dialog_script.DialogScriptInternalItem(
                mock_parm,
                mock_code,
                mock_start_offset,
                mock_end_offset,
                mock_display_name,
                write_back=mock_write_back,
            )

            mock_super_init.assert_called_with(write_back=mock_write_back)

        assert inst._code == mock_code
        assert inst._end_offset == mock_end_offset
        assert inst._parm == mock_parm
        assert inst._start_offset == mock_start_offset
        assert inst._name == "first"
        assert inst._display_hint == ""
        assert inst._display_name == mock_display_name + "_" + "first"
        assert inst._post_processed_code == mock_code

        assert ignored == ["hou"]

        mock_search.assert_called_with(mock_parm)

    # Non-public methods

    @pytest.mark.parametrize(
        "code, expected_code, is_single_line",
        (
            ("foo", "foo", True),
            ("foo", "foo", False),
            ("bar\n", "bar", True),
            ("bar\n", "bar", False),
        ),
    )
    def test__load_contents(
        self, mocker, init_internal_item, code, expected_code, is_single_line
    ):
        """Test DialogScriptInternalItem._load_contents."""
        mock_temp_path = mocker.MagicMock(spec=pathlib.Path)

        mock_handle = mocker.mock_open()
        mock_handle.return_value.read.return_value = code

        mock_temp_path.open = mock_handle

        mock_escape = mocker.patch(
            "houdini_package_runner.items.dialog_script._escape_contents_for_single_line"
        )

        inst = init_internal_item()
        inst._code = code
        inst._is_single_line = is_single_line

        result = inst._load_contents(mock_temp_path)

        if is_single_line:
            assert result == mock_escape.return_value
            mock_escape.assert_called_with(expected_code)

        else:
            assert result == expected_code

    def test__post_process_contents(self, mocker, init_internal_item):
        """Test DialogScriptInternalItem._post_process_contents."""
        contents = mocker.MagicMock(spec=str)

        inst = init_internal_item()
        result = inst._post_process_contents(contents)

        assert result == contents

    @pytest.mark.parametrize(
        "code, expected_code",
        (
            ("foo", "foo\n"),
            ("bar\n", "bar\n"),
        ),
    )
    def test__write_contents(self, mocker, init_internal_item, code, expected_code):
        """Test DialogScriptInternalItem._write_contents."""
        mock_temp_path = mocker.MagicMock(spec=pathlib.Path)

        mock_handle = mocker.mock_open()

        mock_temp_path.open = mock_handle

        inst = init_internal_item()
        inst._code = code

        inst._write_contents(mock_temp_path)

        mock_handle.return_value.write.assert_called_with(expected_code)

    # Properties

    def test_code(self, mocker, init_internal_item):
        """Test DialogScriptInternalItem.code."""
        mock_code = mocker.MagicMock(spec=str)

        inst = init_internal_item()
        inst._code = mock_code

        assert inst.code == mock_code

        with pytest.raises(AttributeError):
            inst.code = "code"

    @pytest.mark.parametrize("has_hint", (True, False))
    def test_display_name(self, mocker, init_internal_item, has_hint):
        """Test DialogScriptInternalItem.display_name."""
        mock_display_name = mocker.MagicMock(spec=str)

        inst = init_internal_item()
        inst._display_name = mock_display_name
        inst._display_hint = "hint" if has_hint else ""

        if has_hint:
            assert inst.display_name == mock_display_name + "_hint"

        else:
            assert inst.display_name == mock_display_name

        with pytest.raises(AttributeError):
            inst.display_name = "display name"

    def test_end_offset(self, mocker, init_internal_item):
        """Test DialogScriptInternalItem.end_offset."""
        mock_end_offset = mocker.MagicMock(spec=int)

        inst = init_internal_item()
        inst._end_offset = mock_end_offset

        assert inst.end_offset == mock_end_offset

        with pytest.raises(AttributeError):
            inst.end_offset = 1

    def test_name(self, mocker, init_internal_item):
        """Test DialogScriptInternalItem.name."""
        mock_name = mocker.MagicMock(spec=str)

        inst = init_internal_item()
        inst._name = mock_name

        assert inst.name == mock_name

        with pytest.raises(AttributeError):
            inst.name = "name"

    def test_parm(self, mocker, init_internal_item):
        """Test DialogScriptInternalItem.parm."""
        mock_parm = mocker.MagicMock(spec=str)

        inst = init_internal_item()
        inst._parm = mock_parm

        assert inst.parm == mock_parm

        with pytest.raises(AttributeError):
            inst.parm = "parm"

    def test_start_offset(self, mocker, init_internal_item):
        """Test DialogScriptInternalItem.start_offset."""
        mock_start_offset = mocker.MagicMock(spec=int)

        inst = init_internal_item()
        inst._start_offset = mock_start_offset

        assert inst.start_offset == mock_start_offset

        with pytest.raises(AttributeError):
            inst.start_offset = 1

    def test_post_processed_code(self, mocker, init_internal_item):
        """Test DialogScriptInternalItem.post_processed_code."""
        mock_post_processed_code = mocker.MagicMock(spec=str)

        inst = init_internal_item()
        inst._post_processed_code = mock_post_processed_code

        assert inst.post_processed_code == mock_post_processed_code

        with pytest.raises(AttributeError):
            inst.post_processed_code = "code"

    # Methods

    @pytest.mark.parametrize(
        "write_back, contents_changed",
        (
            (False, False),
            (True, False),
            (True, True),
        ),
    )
    def test_process(self, mocker, init_internal_item, write_back, contents_changed):
        """Test DialogScriptInternalItem.process."""
        mock_temp_path = mocker.MagicMock(spec=pathlib.Path)

        mock_temp_dir = mocker.MagicMock(spec=pathlib.Path)
        mock_temp_dir.__truediv__.return_value = mock_temp_path

        mock_runner = mocker.MagicMock(
            spec=houdini_package_runner.runners.base.HoudiniPackageRunner
        )
        mock_runner.temp_dir = mock_temp_dir

        mock_code = mocker.MagicMock(spec=str)

        mock_contents = mocker.MagicMock(spec=str) if contents_changed else mock_code

        mock_write = mocker.patch.object(
            houdini_package_runner.items.dialog_script.DialogScriptInternalItem,
            "_write_contents",
        )

        mock_load = mocker.patch.object(
            houdini_package_runner.items.dialog_script.DialogScriptInternalItem,
            "_load_contents",
            return_value=mock_contents,
        )

        mock_post = mocker.patch.object(
            houdini_package_runner.items.dialog_script.DialogScriptInternalItem,
            "_post_process_contents",
        )

        inst = init_internal_item()
        inst._contents_changed = False
        inst._code = mock_code
        inst._post_processed_code = mock_code
        inst._write_back = write_back
        inst._display_name = "display_name"
        inst._display_hint = ""

        result = inst.process(mock_runner)

        assert result == mock_runner.process_path.return_value

        mock_temp_dir.__truediv__.assert_called_with("display_name.py")

        mock_write.assert_called_with(mock_temp_path)

        mock_runner.process_path.assert_called_with(mock_temp_path, inst)

        if write_back:
            mock_load.assert_called_with(mock_temp_path)
            if contents_changed:
                assert inst._post_processed_code == mock_post.return_value
                assert inst._contents_changed

                mock_post.assert_called_with(mock_contents)

            else:
                assert not inst._contents_changed


class TestDialogScriptCallbackItem:
    """Test houdini_package_runner.items.dialog_script.DialogScriptCallbackItem."""

    @pytest.mark.parametrize("pass_defaults", (True, False))
    def test___init__(self, mocker, pass_defaults):
        """Test object initialization."""
        mock_start_offset = mocker.MagicMock(spec=int)
        mock_end_offset = mocker.MagicMock(spec=int)

        mock_get_offset = mocker.patch(
            "houdini_package_runner.items.dialog_script._get_ds_file_offset",
            return_value=[mock_start_offset, mock_end_offset],
        )

        mock_super_init = mocker.patch.object(
            houdini_package_runner.items.dialog_script.DialogScriptInternalItem,
            "__init__",
        )

        ignored = []

        mocker.patch.object(
            houdini_package_runner.items.dialog_script.DialogScriptCallbackItem,
            "ignored_builtins",
            ignored,
        )

        mock_parm = mocker.MagicMock(spec=str)
        mock_code = mocker.MagicMock(spec=str)
        mock_parm_start = mocker.MagicMock(spec=int)
        mock_span = mocker.MagicMock(spec=tuple)
        mock_display_name = mocker.MagicMock(spec=str)
        mock_write_back = mocker.MagicMock(spec=bool)

        if pass_defaults:
            inst = houdini_package_runner.items.dialog_script.DialogScriptCallbackItem(
                mock_parm, mock_code, mock_parm_start, mock_span, mock_display_name
            )
            mock_super_init.assert_called_with(
                mock_parm,
                mock_code,
                mock_start_offset,
                mock_end_offset,
                mock_display_name,
                write_back=False,
            )

        else:
            inst = houdini_package_runner.items.dialog_script.DialogScriptCallbackItem(
                mock_parm,
                mock_code,
                mock_parm_start,
                mock_span,
                mock_display_name,
                write_back=mock_write_back,
            )
            mock_super_init.assert_called_with(
                mock_parm,
                mock_code,
                mock_start_offset,
                mock_end_offset,
                mock_display_name,
                write_back=mock_write_back,
            )

        mock_get_offset.assert_called_with(mock_parm_start, mock_span)

        assert inst._display_hint == "callback"
        assert inst._is_single_line

        assert ignored == ["kwargs"]


class TestDialogScriptDefaultExpressionItem:
    """Test houdini_package_runner.items.dialog_script.DialogScriptDefaultExpressionItem."""

    @pytest.mark.parametrize("pass_defaults", (True, False))
    def test___init__(self, mocker, pass_defaults):
        """Test object initialization."""
        mock_start_offset = mocker.MagicMock(spec=int)
        mock_end_offset = mocker.MagicMock(spec=int)

        mock_get_offset = mocker.patch(
            "houdini_package_runner.items.dialog_script._get_ds_file_offset",
            return_value=[mock_start_offset, mock_end_offset],
        )

        mock_super_init = mocker.patch.object(
            houdini_package_runner.items.dialog_script.DialogScriptInternalItem,
            "__init__",
        )

        mock_parm = mocker.MagicMock(spec=str)
        mock_code = mocker.MagicMock(spec=str)
        mock_parm_start = mocker.MagicMock(spec=int)
        mock_span = mocker.MagicMock(spec=tuple)
        mock_display_name = mocker.MagicMock(spec=str)
        mock_write_back = mocker.MagicMock(spec=bool)

        if pass_defaults:
            inst = houdini_package_runner.items.dialog_script.DialogScriptDefaultExpressionItem(
                mock_parm, mock_code, mock_parm_start, mock_span, mock_display_name
            )
            mock_super_init.assert_called_with(
                mock_parm,
                mock_code,
                mock_start_offset,
                mock_end_offset,
                mock_display_name,
                write_back=False,
            )

        else:
            inst = houdini_package_runner.items.dialog_script.DialogScriptDefaultExpressionItem(
                mock_parm,
                mock_code,
                mock_parm_start,
                mock_span,
                mock_display_name,
                write_back=mock_write_back,
            )
            mock_super_init.assert_called_with(
                mock_parm,
                mock_code,
                mock_start_offset,
                mock_end_offset,
                mock_display_name,
                write_back=mock_write_back,
            )

        mock_get_offset.assert_called_with(mock_parm_start, mock_span)

        assert inst._display_hint == "default"
        assert inst._is_single_line


class TestDialogScriptMenuScriptItem:
    """Test houdini_package_runner.items.dialog_script.DialogScriptMenuScriptItem."""

    @pytest.mark.parametrize("pass_defaults", (True, False))
    def test___init__(self, mocker, pass_defaults):
        """Test object initialization."""
        mock_start_offset = mocker.MagicMock(spec=int)
        mock_end_offset = mocker.MagicMock(spec=int)

        mock_get_offset = mocker.patch(
            "houdini_package_runner.items.dialog_script._get_ds_file_offset",
            return_value=[mock_start_offset, mock_end_offset],
        )

        mock_super_init = mocker.patch.object(
            houdini_package_runner.items.dialog_script.DialogScriptInternalItem,
            "__init__",
        )

        ignored = []

        mocker.patch.object(
            houdini_package_runner.items.dialog_script.DialogScriptMenuScriptItem,
            "ignored_builtins",
            ignored,
        )

        mock_parm = mocker.MagicMock(spec=str)
        mock_parm_start = mocker.MagicMock(spec=int)
        mock_display_name = mocker.MagicMock(spec=str)
        mock_data = mocker.MagicMock(
            spec=houdini_package_runner.items.dialog_script.PythonMenuScriptResult
        )
        mock_write_back = mocker.MagicMock(spec=bool)

        if pass_defaults:
            inst = (
                houdini_package_runner.items.dialog_script.DialogScriptMenuScriptItem(
                    mock_parm, mock_parm_start, mock_display_name, mock_data
                )
            )
            mock_super_init.assert_called_with(
                mock_parm,
                mock_data.menu_script,
                mock_start_offset,
                mock_end_offset,
                mock_display_name,
                write_back=False,
            )

        else:
            inst = (
                houdini_package_runner.items.dialog_script.DialogScriptMenuScriptItem(
                    mock_parm,
                    mock_parm_start,
                    mock_display_name,
                    mock_data,
                    write_back=mock_write_back,
                )
            )
            mock_super_init.assert_called_with(
                mock_parm,
                mock_data.menu_script,
                mock_start_offset,
                mock_end_offset,
                mock_display_name,
                write_back=mock_write_back,
            )

        mock_get_offset.assert_called_with(
            mock_parm_start, mock_data.span, inclusive=True
        )

        assert inst._display_hint == "menu_script"
        assert inst._menu_script_data == mock_data
        assert ignored == ["kwargs"]

    @pytest.mark.parametrize(
        "use_tabs, expected",
        (
            (True, '[ "foo" ]\n\t\t\t\t[ "bar" ]\n\t\t\t\t[ "baz" ]\n'),
            (False, '[ "foo" ]\n    [ "bar" ]\n    [ "baz" ]\n'),
        ),
    )
    def test__post_process_contents(self, mocker, init_menu_item, use_tabs, expected):
        """Test DialogScriptMenuScriptItem._post_process_contents."""
        mock_data = mocker.MagicMock(
            spec=houdini_package_runner.items.dialog_script.PythonMenuScriptResult
        )
        mock_data.uses_tabs = use_tabs
        mock_data.indent = 4

        contents = "foo\nbar\nbaz"

        inst = init_menu_item()
        inst._menu_script_data = mock_data

        result = inst._post_process_contents(contents)

        assert result == expected

    # Properties

    def test_menu_script_data(self, mocker, init_menu_item):
        """Test DialogScriptMenuScriptItem.menu_script_data."""
        mock_data = mocker.MagicMock(
            spec=houdini_package_runner.items.dialog_script.PythonMenuScriptResult
        )

        inst = init_menu_item()
        inst._menu_script_data = mock_data

        assert inst.menu_script_data == mock_data

        with pytest.raises(AttributeError):
            inst.menu_script_data = "some name"


@pytest.mark.parametrize(
    "value, start, expected",
    (
        ("ab\r\r\nfoo", 0, 0),
        ("\r\r\nfoo", 0, 3),
        ("\r\r\nfoo", 10, 10),
    ),
)
def test__discard_newlines(value, start, expected):
    """Test houdini_package_runner.items.dialog_script._discard_newlines."""
    result = houdini_package_runner.items.dialog_script._discard_newlines(value, start)
    assert result == expected


def test__escape_contents_for_single_line():
    """Test houdini_package_runner.items.dialog_script._escape_contents_for_single_line."""
    test_str = 'foo\rbar\n"thing"'

    result = (
        houdini_package_runner.items.dialog_script._escape_contents_for_single_line(
            test_str
        )
    )

    assert result == 'foo\\rbar\\n\\"thing\\"'


@pytest.mark.parametrize(
    "value, expected",
    (
        ('parmtag { "script_callback_language" "python" }', "python"),
        ('parmtag { "script_callback_language" "hscript" }', "hscript"),
        ("parmtag { }", None),
    ),
)
def test__get_callback_language(value, expected):
    """Test houdini_package_runner.items.dialog_script._get_callback_language."""
    result = houdini_package_runner.items.dialog_script._get_callback_language(value)

    assert result == expected


@pytest.mark.parametrize(
    "parm_start, span, inclusive, expected",
    (
        (
            (0, (3, 10), True, (3, 10)),
            (0, (3, 10), False, (4, 9)),
        )
    ),
)
def test__get_ds_file_offset(parm_start, span, inclusive, expected):
    """Test houdini_package_runner.items.dialog_script._get_ds_file_offset."""
    result = houdini_package_runner.items.dialog_script._get_ds_file_offset(
        parm_start, span, inclusive
    )

    assert result == expected


@pytest.mark.parametrize(
    "is_python, has_callback",
    (
        (True, True),
        (True, False),
        (False, False),
    ),
)
def test__get_callback_items(mocker, is_python, has_callback):
    """Test houdini_package_runner.items.dialog_script._get_callback_items."""
    mock_parm = mocker.MagicMock(spec=str)
    mock_parm_start = mocker.MagicMock(spec=int)
    mock_name = mocker.MagicMock(spec=str)

    mock_script = mocker.MagicMock(spec=str)
    mock_span = mocker.MagicMock(spec=tuple)

    language = "python" if is_python else "hscript"
    mock_get_lang = mocker.patch(
        "houdini_package_runner.items.dialog_script._get_callback_language",
        return_value=language,
    )

    script = (mock_script, mock_span) if has_callback else None

    mock_get_script = mocker.patch(
        "houdini_package_runner.items.dialog_script._get_script_callback",
        return_value=script,
    )

    mock_callback_item = mocker.patch(
        "houdini_package_runner.items.dialog_script.DialogScriptCallbackItem"
    )

    result = houdini_package_runner.items.dialog_script._get_callback_items(
        mock_parm, mock_parm_start, mock_name
    )

    if is_python:
        mock_get_script.assert_called_with(mock_parm)

    if is_python and has_callback:
        assert result == [mock_callback_item.return_value]

        mock_callback_item.assert_called_with(
            mock_parm, mock_script, mock_parm_start, mock_span, mock_name
        )

    else:
        assert not result

        mock_callback_item.assert_not_called()

    mock_get_lang.assert_called_with(mock_parm)


def test__get_default_python_expressions(shared_datadir):
    """Test houdini_package_runner.items.dialog_script._get_default_python_expressions."""
    test_path = shared_datadir / "test__get_default_python_expressions.ds"

    with test_path.open() as handle:
        contents = handle.read()

    result = houdini_package_runner.items.dialog_script._get_default_python_expressions(
        contents
    )

    assert result == (('hou.hscript("$FF")', (123, 145)),)


def test__get_expression_items(mocker):
    """Test houdini_package_runner.items.dialog_script._get_expression_items."""
    mock_parm = mocker.MagicMock(spec=str)
    mock_parm_start = mocker.MagicMock(spec=int)
    mock_name = mocker.MagicMock(spec=str)

    mock_expr = mocker.MagicMock(spec=str)
    mock_span = mocker.MagicMock(spec=tuple)

    mock_default_expressions = [(mock_expr, mock_span)]
    mock_get_exprs = mocker.patch(
        "houdini_package_runner.items.dialog_script._get_default_python_expressions",
        return_value=mock_default_expressions,
    )

    mock_expr_item = mocker.patch(
        "houdini_package_runner.items.dialog_script.DialogScriptDefaultExpressionItem"
    )

    result = houdini_package_runner.items.dialog_script._get_expression_items(
        mock_parm, mock_parm_start, mock_name
    )

    assert result == [mock_expr_item.return_value]

    mock_get_exprs.assert_called_with(mock_parm)

    mock_expr_item.assert_called_with(
        mock_parm, mock_expr, mock_parm_start, mock_span, mock_name
    )


@pytest.mark.parametrize("script_exists", (True, False))
def test__get_menu_items(mocker, script_exists):
    """Test houdini_package_runner.items.dialog_script._get_menu_items."""
    mock_parm = mocker.MagicMock(spec=str)
    mock_parm_start = mocker.MagicMock(spec=int)
    mock_name = mocker.MagicMock(spec=str)

    mock_item = (
        mocker.MagicMock(
            spec=houdini_package_runner.items.dialog_script.PythonMenuScriptResult
        )
        if script_exists
        else None
    )

    mock_get_script = mocker.patch(
        "houdini_package_runner.items.dialog_script._get_python_menu_script",
        return_value=mock_item,
    )

    mock_ds_item = mocker.patch(
        "houdini_package_runner.items.dialog_script.DialogScriptMenuScriptItem"
    )

    result = houdini_package_runner.items.dialog_script._get_menu_items(
        mock_parm, mock_parm_start, mock_name
    )

    if script_exists:
        assert result == [mock_ds_item.return_value]
        mock_ds_item.assert_called_with(
            mock_parm, mock_parm_start, mock_name, mock_item
        )

    else:
        assert not result

    mock_get_script.assert_called_with(mock_parm)


@pytest.mark.parametrize(
    "test_file, expected",
    (
        ("tabs.ds", ((84, 134), 2, True)),
        ("spaces.ds", ((129, 199), 12, False)),
        (None, ()),
    ),
)
def test__get_python_menu_script(shared_datadir, test_file, expected):
    """Test houdini_package_runner.items.dialog_script._get_python_menu_script."""
    expected_script = """import os

return [1,2,3,4]"""

    if test_file is not None:
        test_path = shared_datadir / "test__get_python_menu_script" / test_file

        with test_path.open() as handle:
            contents = handle.read()
    else:
        contents = ""

    result = houdini_package_runner.items.dialog_script._get_python_menu_script(
        contents
    )

    if test_file is not None:
        assert result.menu_script == expected_script
        assert result.span == expected[0]
        assert result.indent == expected[1]
        assert result.uses_tabs == expected[2]

    else:
        assert result is None


@pytest.mark.parametrize("has_match", (True, False))
def test__get_script_callback(shared_datadir, has_match):
    """Test houdini_package_runner.items.dialog_script._get_script_callback."""

    if has_match:
        test_path = shared_datadir / "test__get_script_callback.ds"

        with test_path.open() as handle:
            contents = handle.read()
    else:
        contents = ""

    result = houdini_package_runner.items.dialog_script._get_script_callback(contents)

    if has_match:
        assert result == ("hou.hm().callback(hou.pwd())", (165, 195))

    else:
        assert result is None
