# -*- coding: utf-8 -*-
from __future__ import print_function

import sys
import traceback

from ..compat import QtCore
from ..compat import QtGui
from ..compat import StringIO
from ..compat import HOST
from ..core.text_transform import comment_line
from ..core.text_transform import indent_line
from ..core.text_transform import uncomment_line
from ..core.text_transform import unindent_line
from ..pycompat import text_type
from ..style import toolbar_icon
from .code_editor import CodeEditor
from .code_editor import ScriptHighlighter


class ScriptEditorWidget(QtGui.QWidget):

    textChanged = QtCore.Signal()
    runFinished = QtCore.Signal(
        bool
    )

    def __init__(
        self,
        language="python",
        toolbox=None,
        parent=None
    ):
        QtGui.QWidget.__init__(
            self,
            parent
        )

        self.toolbox = toolbox
        self._language = "python"
        self._last_find = ""

        self.build_ui()
        self.set_language(
            language
        )

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def build_ui(self):
        root = QtGui.QVBoxLayout(
            self
        )
        root.setContentsMargins(
            0,
            0,
            0,
            0
        )
        root.setSpacing(
            4
        )

        toolbar = QtGui.QHBoxLayout()
        toolbar.setSpacing(
            2
        )

        self._add_tool_button(
            toolbar,
            "undo",
            "Undo",
            self.undo
        )
        self._add_tool_button(
            toolbar,
            "redo",
            "Redo",
            self.redo
        )

        toolbar.addSpacing(
            4
        )

        self._add_tool_button(
            toolbar,
            "cut",
            "Cut",
            self.cut
        )
        self._add_tool_button(
            toolbar,
            "copy",
            "Copy",
            self.copy
        )
        self._add_tool_button(
            toolbar,
            "paste",
            "Paste",
            self.paste
        )

        toolbar.addSpacing(
            4
        )

        self._add_tool_button(
            toolbar,
            "find",
            "Find text",
            self.find_text
        )
        self._add_tool_button(
            toolbar,
            "find_next",
            "Find next",
            self.find_next
        )

        toolbar.addSpacing(
            4
        )

        self._add_tool_button(
            toolbar,
            "comment",
            "Comment selected/current lines",
            self.comment
        )
        self._add_tool_button(
            toolbar,
            "uncomment",
            "Uncomment selected/current lines",
            self.uncomment
        )
        self._add_tool_button(
            toolbar,
            "indent",
            "Indent selected/current lines",
            self.indent
        )
        self._add_tool_button(
            toolbar,
            "unindent",
            "Unindent selected/current lines",
            self.unindent
        )

        toolbar.addSpacing(
            4
        )

        self.run_button = self._add_tool_button(
            toolbar,
            "run",
            "Run script",
            self.run
        )

        toolbar.addStretch(
            1
        )

        root.addLayout(
            toolbar
        )

        self.splitter = QtGui.QSplitter(
            QtCore.Qt.Vertical
        )

        self.editor = CodeEditor()
        self.highlighter = ScriptHighlighter(
            self.editor.document(),
            "python"
        )

        self.output = QtGui.QPlainTextEdit()
        self.output.setReadOnly(
            True
        )
        self.output.setLineWrapMode(
            QtGui.QPlainTextEdit.NoWrap
        )

        output_font = QtGui.QFont(
            "Consolas"
        )
        output_font.setStyleHint(
            QtGui.QFont.Monospace
        )
        output_font.setPointSize(
            9
        )
        self.output.setFont(
            output_font
        )

        self.splitter.addWidget(
            self.editor
        )
        self.splitter.addWidget(
            self.output
        )
        self.splitter.setSizes([
            360,
            105
        ])

        root.addWidget(
            self.splitter,
            1
        )

        status_row = QtGui.QHBoxLayout()
        status_row.setSpacing(
            4
        )

        clear_output = self._tool_button(
            "clear",
            "Clear Output",
            self.output.clear
        )

        self.status_label = QtGui.QLabel(
            "Ready"
        )
        self.status_label.setObjectName(
            "EditorStatus"
        )

        self.cursor_label = QtGui.QLabel(
            "Ln 1, Col 1"
        )
        self.cursor_label.setObjectName(
            "EditorStatus"
        )

        status_row.addWidget(
            clear_output
        )
        status_row.addWidget(
            self.status_label
        )
        status_row.addStretch(
            1
        )
        status_row.addWidget(
            self.cursor_label
        )

        root.addLayout(
            status_row
        )

        self.editor.textChanged.connect(
            self.textChanged.emit
        )
        self.editor.cursorPositionChanged.connect(
            self.update_cursor_position
        )

    def _tool_button(
        self,
        icon_kind,
        tooltip,
        callback
    ):
        button = QtGui.QToolButton()
        button.setObjectName(
            "IconButton"
        )
        button.setIcon(
            toolbar_icon(
                icon_kind
            )
        )
        button.setIconSize(
            QtCore.QSize(
                18,
                18
            )
        )
        button.setFixedSize(
            26,
            26
        )
        button.setToolTip(
            tooltip
        )
        button.clicked.connect(
            callback
        )
        return button

    def _add_tool_button(
        self,
        layout,
        icon_kind,
        tooltip,
        callback
    ):
        button = self._tool_button(
            icon_kind,
            tooltip,
            callback
        )
        layout.addWidget(
            button
        )
        return button

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_language(
        self,
        language
    ):
        language = text_type(
            language or "python"
        ).lower()

        if language not in (
            "python",
            "mel"
        ):
            language = "python"

        self._language = language

        if hasattr(
            self,
            "highlighter"
        ):
            self.highlighter.set_language(
                language
            )

    def language(self):
        return self._language

    def setPlainText(
        self,
        value
    ):
        self.editor.setPlainText(
            text_type(
                value or ""
            )
        )

    def toPlainText(self):
        return text_type(
            self.editor.toPlainText()
        )

    def set_toolbox(
        self,
        toolbox
    ):
        self.toolbox = toolbox

    def set_output_visible(
        self,
        visible
    ):
        self.output.setVisible(
            bool(
                visible
            )
        )

    # ------------------------------------------------------------------
    # Standard editing
    # ------------------------------------------------------------------

    def undo(self):
        self.editor.undo()

    def redo(self):
        self.editor.redo()

    def cut(self):
        self.editor.cut()

    def copy(self):
        self.editor.copy()

    def paste(self):
        self.editor.paste()

    def update_cursor_position(self):
        try:
            cursor = self.editor.textCursor()

            self.cursor_label.setText(
                "Ln {0}, Col {1}".format(
                    cursor.blockNumber() + 1,
                    cursor.columnNumber() + 1
                )
            )
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Find
    # ------------------------------------------------------------------

    def _dialog_text(
        self,
        value
    ):
        try:
            value = value.toString()
        except Exception:
            pass

        return text_type(
            value or ""
        )

    def find_text(self):
        value, ok = QtGui.QInputDialog.getText(
            self,
            "Find",
            "Find:"
        )

        if not ok:
            return False

        value = self._dialog_text(
            value
        )

        if not value:
            return False

        self._last_find = value

        if not self._find_with_wrap(
            value
        ):
            self.status_label.setText(
                "Not found: {0}".format(
                    value
                )
            )
            return False

        self.status_label.setText(
            "Found: {0}".format(
                value
            )
        )
        return True

    def find_next(self):
        if not self._last_find:
            return self.find_text()

        found = self._find_with_wrap(
            self._last_find
        )

        self.status_label.setText(
            (
                "Found: {0}"
                if found
                else "Not found: {0}"
            ).format(
                self._last_find
            )
        )

        return found

    def _find_with_wrap(
        self,
        value
    ):
        if self.editor.find(
            value
        ):
            return True

        cursor = self.editor.textCursor()
        cursor.movePosition(
            QtGui.QTextCursor.Start
        )
        self.editor.setTextCursor(
            cursor
        )

        return bool(
            self.editor.find(
                value
            )
        )

    # ------------------------------------------------------------------
    # Line transforms
    # ------------------------------------------------------------------

    def _selected_blocks(self):
        cursor = self.editor.textCursor()

        start = cursor.selectionStart()
        end = cursor.selectionEnd()

        document = self.editor.document()

        start_block = document.findBlock(
            start
        )
        end_block = document.findBlock(
            end
        )

        if (
            end > start and
            end_block.position() == end
        ):
            end_block = end_block.previous()

        return (
            cursor,
            start_block,
            end_block
        )

    def _transform_lines(
        self,
        transform
    ):
        (
            original_cursor,
            start_block,
            end_block
        ) = self._selected_blocks()

        if not start_block.isValid():
            return

        had_selection = original_cursor.hasSelection()
        start_pos = start_block.position()

        if end_block.isValid():
            end_pos = (
                end_block.position() +
                end_block.length() -
                1
            )
        else:
            end_pos = start_pos

        cursor = QtGui.QTextCursor(
            self.editor.document()
        )
        cursor.setPosition(
            start_pos
        )
        cursor.setPosition(
            end_pos,
            QtGui.QTextCursor.KeepAnchor
        )

        selected = text_type(
            cursor.selectedText()
        ).replace(
            u"\u2029",
            "\n"
        )

        lines = selected.split(
            "\n"
        )

        new_text = "\n".join(
            transform(
                line
            )
            for line in lines
        )

        cursor.beginEditBlock()
        cursor.insertText(
            new_text
        )
        cursor.endEditBlock()

        if had_selection:
            cursor.setPosition(
                start_pos
            )
            cursor.setPosition(
                start_pos + len(
                    new_text
                ),
                QtGui.QTextCursor.KeepAnchor
            )

        self.editor.setTextCursor(
            cursor
        )

    def comment(self):
        language = self.language()

        self._transform_lines(
            lambda line:
            comment_line(
                line,
                language
            )
        )

    def uncomment(self):
        language = self.language()

        self._transform_lines(
            lambda line:
            uncomment_line(
                line,
                language
            )
        )

    def indent(self):
        self._transform_lines(
            lambda line:
            indent_line(
                line,
                4
            )
        )

    def unindent(self):
        self._transform_lines(
            lambda line:
            unindent_line(
                line,
                4
            )
        )

    # ------------------------------------------------------------------
    # Run / Output
    # ------------------------------------------------------------------

    def append_output(
        self,
        value
    ):
        if value is None:
            return

        value = text_type(
            value
        )

        if not value:
            return

        self.output.moveCursor(
            QtGui.QTextCursor.End
        )
        self.output.insertPlainText(
            value
        )

        if not value.endswith(
            "\n"
        ):
            self.output.insertPlainText(
                "\n"
            )

        self.output.moveCursor(
            QtGui.QTextCursor.End
        )

    def run(self):
        code = self.toPlainText()

        self.output.clear()
        self.status_label.setText(
            "Running..."
        )

        if not code.strip():
            self.status_label.setText(
                "Nothing to run"
            )
            self.runFinished.emit(
                True
            )
            return True

        if self.language() != "python":
            return self._run_native(
                code
            )

        return self._run_python(
            code
        )

    def _run_native(
        self,
        code
    ):
        try:
            result = HOST.execute_native(
                self.language(),
                code
            )

            if result is not None:
                self.append_output(
                    result
                )

            if not self.output.toPlainText():
                self.append_output(
                    "Finished without output."
                )

            self.status_label.setText(
                "Finished"
            )
            self.runFinished.emit(
                True
            )
            return True

        except Exception:
            self.append_output(
                traceback.format_exc()
            )
            self.status_label.setText(
                "Error"
            )
            self.runFinished.emit(
                False
            )
            return False

    def _run_python(
        self,
        code
    ):
        old_stdout = sys.stdout
        old_stderr = sys.stderr

        stdout_buffer = StringIO()
        stderr_buffer = StringIO()

        namespace = {
            "__name__": "__script_toolbox_editor__",
            "toolbox": self.toolbox,
        }
        namespace.update(
            HOST.script_namespace()
        )

        success = True

        try:
            sys.stdout = stdout_buffer
            sys.stderr = stderr_buffer

            compiled = compile(
                code,
                "<Script Toolbox Editor>",
                "exec"
            )

            eval(
                compiled,
                namespace,
                namespace
            )

        except Exception:
            success = False
            traceback.print_exc()

        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        stdout_value = stdout_buffer.getvalue()
        stderr_value = stderr_buffer.getvalue()

        if stdout_value:
            self.append_output(
                stdout_value
            )

        if stderr_value:
            self.append_output(
                stderr_value
            )

        if (
            not stdout_value and
            not stderr_value
        ):
            self.append_output(
                "Finished without output."
            )

        self.status_label.setText(
            "Finished"
            if success
            else "Error"
        )
        self.runFinished.emit(
            success
        )
        return success


__all__ = [
    "ScriptEditorWidget",
]
