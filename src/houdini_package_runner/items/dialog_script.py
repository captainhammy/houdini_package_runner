"""This module contains runnable items based on Houdini digital asset's DialogScript."""

# =============================================================================
# IMPORTS
# =============================================================================

# Future
from __future__ import annotations

# Standard Library
import abc
import operator
from collections import namedtuple
from typing import TYPE_CHECKING, List, Optional, Tuple

# Third Party
import pyparsing  # type: ignore

# Houdini Package Runner
from houdini_package_runner.items.base import BaseFileItem, BaseItem

# Imports for type checking.
if TYPE_CHECKING:
    import pathlib

    import houdini_package_runner.runners.base


# =============================================================================
# GLOBALS
# =============================================================================

# The majority of the code below to do the parsing of the DialogScript file
# is lifted from Houdini's $HFS/bin/py23convert.py tool.  A big thanks to them
# for the unenviable task of writing this such that we may repurpose it for
# our own use.

_DS_NAME_EXPR_GRAMMAR = (
    pyparsing.Keyword("name").suppress() + pyparsing.QuotedString('"')
).parseWithTabs()

_DS_DEF_EXPR_TYPED = (
    pyparsing.Literal("[").suppress()
    + pyparsing.Group(
        pyparsing.locatedExpr(
            pyparsing.QuotedString(quoteChar='"', escChar="\\", multiline=True)
        )
        + pyparsing.Word(pyparsing.alphas + "-")
    )
    + pyparsing.Literal("]").suppress()
)

_DS_DEF_EXPR_LIT = (
    pyparsing.QuotedString(quoteChar='"', escChar="\\", multiline=True).suppress()
    | pyparsing.Word(pyparsing.nums).suppress()
)

_DS_DEF_EXPR_GRAMMAR = (
    pyparsing.Keyword("default").suppress()
    + pyparsing.Literal("{").suppress()
    + pyparsing.OneOrMore(_DS_DEF_EXPR_TYPED | _DS_DEF_EXPR_LIT)
    + pyparsing.Literal("}").suppress()
).parseWithTabs()

_DS_CB_SCRIPT_LANG_GRAMMAR = (
    pyparsing.Keyword("parmtag").suppress()
    + pyparsing.Literal("{").suppress()
    + pyparsing.Literal('"script_callback_language"').suppress()
    + pyparsing.QuotedString('"')
    + pyparsing.Literal("}").suppress()
)

_DS_CB_SCRIPT_GRAMMAR = (
    pyparsing.Keyword("parmtag").suppress()
    + pyparsing.Literal("{").suppress()
    + pyparsing.Literal('"script_callback"').suppress()
    + pyparsing.locatedExpr(
        pyparsing.QuotedString(quoteChar='"', escChar="\\", multiline=True)
    )
    + pyparsing.Literal("}").suppress()
).parseWithTabs()

_DS_MENU_PY = pyparsing.locatedExpr(
    pyparsing.Literal("[").suppress()
    + pyparsing.QuotedString(quoteChar='"', escChar="\\")
    + pyparsing.Literal("]").suppress()
).parseWithTabs()

_DS_MENU_GRAMMAR = (
    pyparsing.Keyword("menu").suppress()
    + pyparsing.Literal("{").suppress()
    + pyparsing.OneOrMore(_DS_MENU_PY)
    + pyparsing.Literal("language").suppress()
    + pyparsing.Literal("python").suppress()
    + pyparsing.Literal("}").suppress()
).parseWithTabs()

_DS_PARM_GRAMMAR = pyparsing.originalTextFor(
    pyparsing.Keyword("parm") + pyparsing.nestedExpr("{", "}")
).parseWithTabs()


PythonMenuScriptResult = namedtuple(
    "PythonMenuScriptResult", ["menu_script", "span", "indent", "uses_tabs"]
)
"""Item to hold menu script information."""


# =============================================================================
# CLASSES
# =============================================================================


class DialogScriptItem(BaseFileItem):
    """Item representing a DialogScript section inside a digital asset definition.

    :param path: The file path to process.
    :param name: The display name for test output.
    :param write_back: Whether the item should write itself back to disk.
    :param source_file: Optional source file for the expanded operator definition.

    """

    def __init__(
        self,
        path: pathlib.Path,
        name: str,
        write_back: bool = False,
        source_file: pathlib.PurePath = None,
    ) -> None:
        super().__init__(path, write_back=write_back)

        self._name = name
        self._source_file = source_file

        # Stash the script contents.
        with self.path.open(encoding="utf-8") as handle:
            self._ds_contents = handle.read()

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.name} ({self.path})>"

    # -------------------------------------------------------------------------
    # NON-PUBLIC METHODS
    # -------------------------------------------------------------------------

    def _gather_items(self) -> Tuple[DialogScriptInternalItem, ...]:
        """Gather the items from the DialogScript to process.

        :return: Any items to be processed.

        """
        items: List[DialogScriptInternalItem] = []

        for match, parm_start, _ in _DS_PARM_GRAMMAR.scanString(self._ds_contents):
            # The block of code related to the parameter definition.
            parm = match.asList()[0]

            items.extend(_get_callback_items(parm, parm_start, self.name))

            items.extend(_get_expression_items(parm, parm_start, self.name))

            items.extend(_get_menu_items(parm, parm_start, self.name))

        # Set the 'write_back' property of all the items if necessary.
        if self.write_back:
            for item in items:
                item.write_back = True

        return tuple(items)

    def _handle_changed_contents(
        self, items_with_changed_contents: List[DialogScriptInternalItem]
    ):
        """Handle writing any items with changed contents to the file.

        :param items_with_changed_contents: A list of items with changed contents.

        """
        items_with_changed_contents.sort(key=operator.attrgetter("start_offset"))

        parts = []

        script_offset = 0

        for item in items_with_changed_contents:
            parts.append(self._ds_contents[script_offset : item.start_offset])
            parts.append(item.post_processed_code)
            script_offset = item.end_offset

        parts.append(self._ds_contents[script_offset:])
        new_dialog_script = "".join(parts)

        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write(new_dialog_script)

    # -------------------------------------------------------------------------
    # PROPERTIES
    # -------------------------------------------------------------------------

    @property
    def name(self) -> str:
        """The display name of the operator."""
        return self._name

    # -------------------------------------------------------------------------
    # METHODS
    # -------------------------------------------------------------------------

    def process(
        self, runner: houdini_package_runner.runners.base.HoudiniPackageRunner
    ) -> int:
        """Process the operator files.

        :param runner: The package runner processing the item.
        :return: The process return code.

        """
        files_to_process = self._gather_items()

        result = 0

        items_with_changed_contents = []

        for file_to_process in files_to_process:
            result |= file_to_process.process(runner)

            if file_to_process.contents_changed:
                items_with_changed_contents.append(file_to_process)

        if self.write_back and items_with_changed_contents:
            self.contents_changed = True
            self._handle_changed_contents(items_with_changed_contents)

        return result


class DialogScriptInternalItem(BaseItem, metaclass=abc.ABCMeta):
    """Base definition for a Python processable item in a DialogScript.

    :param parm: The source parameter definition.
    :param code: The Python code for the item.
    :param start_offset: There parameter definition start offset.
    :param end_offset: There parameter definition end offset.
    :param display_name: The item display name.
    :param write_back: Whether the item should write itself back to disk.

    """

    def __init__(
        self,
        parm: str,
        code: str,
        start_offset: int,
        end_offset: int,
        display_name: str,
        write_back: bool = False,
    ) -> None:
        super().__init__(write_back=write_back)

        self._code = code
        self._end_offset = end_offset
        self._parm = parm
        self._start_offset = start_offset

        name = _DS_NAME_EXPR_GRAMMAR.searchString(parm)[0][0]

        self._name = name
        self._display_hint = ""
        self._display_name = display_name + "_" + name

        self._post_processed_code = code

        # The 'hou' module is always available in these items.
        self.ignored_builtins.append("hou")

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.display_name}>"

    # -------------------------------------------------------------------------
    # NON-PUBLIC METHODS
    # -------------------------------------------------------------------------

    def _load_contents(self, temp_path: pathlib.Path) -> str:
        """Load the contents from the temp path.

        :param temp_path: The item file path.
        :return: The file contents.

        """
        with temp_path.open("r") as handle:
            contents = handle.read()

        # Strip any final newline that we probably added above.
        if contents.endswith("\n"):
            contents = contents[:-1]

        if self.is_single_line:
            contents = _escape_contents_for_single_line(contents)

        return contents

    def _post_process_contents(  # pylint: disable=no-self-use
        self, contents: str
    ) -> str:
        """Perform any post-processing on the contents.

        :param contents: The script contents.
        :return: The processed contents.

        """
        return contents

    def _write_contents(self, temp_path: pathlib.Path) -> None:
        """Write the contents of the item to the temp path.

        :param temp_path: The item file path.
        :return:

        """
        code = self.code

        # If the code blob does not end with a new line it can cause problems with
        # runners such as black.  Add a new line at the end of the code to more properly
        # resemble an actual file to be processed.
        if not code.endswith("\n"):
            code += "\n"

        # Dump the code to the temp file, so it can be processed.
        with temp_path.open("w") as handle:
            handle.write(code)

    # -------------------------------------------------------------------------
    # PROPERTIES
    # -------------------------------------------------------------------------

    @property
    def code(self) -> str:
        """The Python code for the item."""
        return self._code

    @property
    def display_name(self) -> str:
        """The item display name."""
        display_name = self._display_name

        if self._display_hint:
            display_name += "__" + self._display_hint

        return display_name

    @property
    def end_offset(self) -> int:
        """There parameter definition end offset."""
        return self._end_offset

    @property
    def name(self) -> str:
        """The parameter name."""
        return self._name

    @property
    def parm(self) -> str:
        """The parameter definition."""
        return self._parm

    @property
    def start_offset(self) -> int:
        """There parameter definition start offset."""
        return self._start_offset

    @property
    def post_processed_code(self) -> str:
        """The post-processing contents"""
        return self._post_processed_code

    # -------------------------------------------------------------------------
    # METHODS
    # -------------------------------------------------------------------------

    def process(
        self, runner: houdini_package_runner.runners.base.HoudiniPackageRunner
    ) -> int:
        """Process an item.

        :param runner: The package runner processing the item.
        :return: The process return code.

        """
        temp_path = runner.temp_dir / f"{self.display_name}.py"

        self._write_contents(temp_path)

        result = runner.process_path(temp_path, self)

        if self.write_back:
            contents = self._load_contents(temp_path)

            if self.code != contents:
                self.contents_changed = True

                self._post_processed_code = self._post_process_contents(contents)

        return result


class DialogScriptCallbackItem(DialogScriptInternalItem):
    """Item to represent and process a parameter's Python callback script.

    :param parm: The source parameter definition.
    :param code: The Python code for the item.
    :param parm_start: The start position of the parm.
    :param span: The span of the parm data.
    :param display_name: The item display name.
    :param write_back: Whether the item should write itself back to disk.

    """

    def __init__(
        self,
        parm: str,
        code: str,
        parm_start: int,
        span: Tuple[int, int],
        display_name: str,
        write_back: bool = False,
    ) -> None:
        start_offset, end_offset = _get_ds_file_offset(parm_start, span)

        super().__init__(
            parm, code, start_offset, end_offset, display_name, write_back=write_back
        )

        self._display_hint = "callback"
        self._is_single_line = True

        # kwargs is always available in callback scripts.
        self.ignored_builtins.append("kwargs")


class DialogScriptDefaultExpressionItem(DialogScriptInternalItem):
    """Item to represent and process a parameter's Python default expression.

    :param parm: The source parameter definition.
    :param code: The Python code for the item.
    :param parm_start: The start position of the parm.
    :param span: The span of the parm data.
    :param display_name: The item display name.
    :param write_back: Whether the item should write itself back to disk.

    """

    def __init__(
        self,
        parm: str,
        code: str,
        parm_start: int,
        span: Tuple[int, int],
        display_name: str,
        write_back: bool = False,
    ) -> None:
        start_offset, end_offset = _get_ds_file_offset(parm_start, span)

        super().__init__(
            parm, code, start_offset, end_offset, display_name, write_back=write_back
        )

        self._display_hint = "default"
        self._is_single_line = True


class DialogScriptMenuScriptItem(DialogScriptInternalItem):
    """Item to represent and process a parameter's Python menu script.

    :param parm: The source parameter definition.
    :param parm_start: The start position of the parm.
    :param display_name: The item display name.
    :param menu_script_data: The Python menu script data
    :param write_back: Whether the item should write itself back to disk.

    """

    def __init__(
        self,
        parm: str,
        parm_start: int,
        display_name: str,
        menu_script_data: PythonMenuScriptResult,
        write_back: bool = False,
    ) -> None:
        start_offset, end_offset = _get_ds_file_offset(
            parm_start, menu_script_data.span, inclusive=True
        )

        super().__init__(
            parm,
            menu_script_data.menu_script,
            start_offset,
            end_offset,
            display_name,
            write_back=write_back,
        )

        self._display_hint = "menu_script"
        self._menu_script_data = menu_script_data

        # kwargs is always available in menu scripts.
        self.ignored_builtins.append("kwargs")

    # -------------------------------------------------------------------------
    # NON-PUBLIC METHODS
    # -------------------------------------------------------------------------

    def _post_process_contents(self, contents: str) -> str:
        """Perform any post-processing on the contents.

        This will ensure the multiline menu script is properly wrapped.

        :param contents: The script contents.
        :return: The processed contents.

        """
        lines = contents.splitlines()
        new_contents = ""

        indent_char = "\t" if self.menu_script_data.uses_tabs else " "
        indent = indent_char * self.menu_script_data.indent

        for i, line in enumerate(lines):
            new_contents += f'{"" if i == 0 else indent}[ "{line}" ]\n'

        return new_contents

    # -------------------------------------------------------------------------
    # PROPERTIES
    # -------------------------------------------------------------------------

    @property
    def menu_script_data(self) -> PythonMenuScriptResult:
        """The Python menu script data."""
        return self._menu_script_data


# =============================================================================
# NON-PUBLIC FUNCTIONS
# =============================================================================


def _discard_newlines(parm: str, start: int) -> int:
    """Discard any newline characters.

    :param parm: The parameter data.
    :param start: The start index.
    :return: The start index offset to discard any newlines

    """
    pos = start

    while pos < len(parm):
        if parm[pos] not in ("\r", "\n"):
            break

        pos += 1

    return pos


def _escape_contents_for_single_line(contents: str) -> str:
    """Escape characters to write as a single line.

    :param contents: The contents to escape.
    :return: The contents with \r, \n and " escaped

    """
    contents = contents.replace("\r", "\\r").replace("\n", "\\n").replace('"', '\\"')

    return contents


def _get_callback_items(
    parm: str, parm_start: int, name: str
) -> List[DialogScriptCallbackItem]:
    """Build a list of any callback items for a parameter.

    :param parm: The parameter data.
    :param parm_start: The start position of the parm.
    :param name: The display name.
    :return: A list of any callback items.

    """
    items = []
    # Get the parameter's callback script language.
    callback_language = _get_callback_language(parm)

    if callback_language == "python":
        # Get the callback script data, if any.
        result = _get_script_callback(parm)

        if result is not None:
            script, script_span = result

            items.append(
                DialogScriptCallbackItem(parm, script, parm_start, script_span, name)
            )

    return items


def _get_callback_language(parm: str) -> Optional[str]:
    """Get a parameter's callback script language.

    :param parm: The parameter data.
    :return: The script callback language.

    """
    for match in _DS_CB_SCRIPT_LANG_GRAMMAR.searchString(parm):
        return match[0]

    return None


def _get_ds_file_offset(
    parm_start: int, span: Tuple[int, int], inclusive: bool = False
) -> Tuple[int, int]:
    """Get the file offsets for the parameter.

    :param parm_start: The start position of the parm.
    :param span: The span of the parm data.
    :param inclusive: Whether to include the start and end chars.
    :return: The file offsets for the parameter.

    """
    extra_offset = 0 if inclusive else 1

    return parm_start + span[0] + extra_offset, parm_start + span[1] - extra_offset


def _get_default_python_expressions(
    parm: str,
) -> Tuple[Tuple[str, Tuple[int, int]], ...]:
    """Get default Python expressions for a parameter tuple.

    :param parm: The parameter data.
    :return: Any default expressions which are Python.

    """
    expressions = []

    for matches in _DS_DEF_EXPR_GRAMMAR.searchString(parm):
        for match in matches:
            (start, expr, end), expr_lang = match

            if expr_lang == "python":
                expressions.append((expr, (start, end)))

    return tuple(expressions)


def _get_expression_items(
    parm: str, parm_start: int, name: str
) -> List[DialogScriptDefaultExpressionItem]:
    """Build a list of any expression items for a parameter.

    :param parm: The parameter data.
    :param parm_start: The start position of the parm.
    :param name: The display name.
    :return: A list of any expression items.

    """
    items = []

    default_python_expressions = _get_default_python_expressions(parm)

    for expr, span in default_python_expressions:
        items.append(
            DialogScriptDefaultExpressionItem(parm, expr, parm_start, span, name)
        )

    return items


def _get_menu_items(
    parm: str, parm_start: int, name: str
) -> List[DialogScriptMenuScriptItem]:
    """Build a list of any menu script items for a parameter.

    :param parm: The parameter data.
    :param parm_start: The start position of the parm.
    :param name: The display name.
    :return: A list of any menu script items.

    """
    items = []

    # Get any Python menu script data if it exists.
    menu_script = _get_python_menu_script(parm)

    if menu_script is not None:
        items.append(DialogScriptMenuScriptItem(parm, parm_start, name, menu_script))

    return items


def _get_python_menu_script(parm: str) -> Optional[PythonMenuScriptResult]:
    """Get any Python menu script data for a parameter.

    :param parm: The parameter data.
    :return: The menu script data if the parameter has a Python one.

    """
    for match in _DS_MENU_GRAMMAR.searchString(parm):
        lines = match.asList()
        start = lines[0][0]
        end = _discard_newlines(parm, lines[-1][2])
        menu_script = "\n".join([line[1] for line in lines])
        indent = 0

        uses_tabs = False

        for i in range(start - 1, 0, -1):  # pragma: no branch
            if parm[i] == " ":
                indent += 1

            elif parm[i] == "\t":
                indent += 1
                uses_tabs = True

            else:
                break

        # There can only be one menu script so return it.
        return PythonMenuScriptResult(menu_script, (start, end), indent, uses_tabs)

    return None


def _get_script_callback(parm: str) -> Optional[Tuple[str, Tuple[int, int]]]:
    """Get the callback script data for a parameter if it has one.

    The result contains the script contents and start/end offset values.

    :param parm: The parameter data.
    :return: The parameter callback script if the parameter has one.

    """
    for match in _DS_CB_SCRIPT_GRAMMAR.searchString(parm):
        # There can only been one callback script entry per parameter.
        start, text, end = match[0]
        return text, (start, end)

    return None
