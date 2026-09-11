# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore
from ..compat import QtGui
from ..core.completion import CONTEXT_IDENTIFIER
from ..core.completion import CONTEXT_ITEM_ARGUMENT
from ..core.completion import CONTEXT_TOOLBOX_MEMBER
from ..core.completion import CompletionEngine
from ..core.completion import EditorItemsProvider
from ..core.completion import SOURCE_TOOLBOX_API
from ..core.completion import ScriptToolboxApiProvider
from ..model import walk_items
from ..pycompat import text_type
from ..style.palette import BORDER_GROUP
from ..style.palette import LIST_HOVER_BG
from ..style.palette import PANEL_BG
from ..style.palette import SELECTION_BG
from ..style.palette import SELECTION_TEXT
from ..style.palette import TEXT_MUTED
from ..style.palette import TEXT_PRIMARY


class CompletionPopup(QtGui.QTreeWidget):

    def __init__(self, editor):
        QtGui.QTreeWidget.__init__(
            self,
            editor.viewport()
        )
        self.editor = editor

        self.setObjectName(
            "CompletionPopup"
        )
        self.setHeaderHidden(
            True
        )
        self.setRootIsDecorated(
            False
        )
        self.setIndentation(
            0
        )
        self.setAlternatingRowColors(
            False
        )
        self.setSelectionMode(
            QtGui.QAbstractItemView.SingleSelection
        )
        self.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff
        )
        self.setFocusPolicy(
            QtCore.Qt.NoFocus
        )
        try:
            self.viewport().setFocusPolicy(
                QtCore.Qt.NoFocus
            )
        except Exception:
            pass

        self.setColumnCount(
            3
        )
        self.setStyleSheet(
            (
                "QTreeWidget#CompletionPopup {"
                " background-color: %s;"
                " border: 1px solid %s;"
                " color: %s;"
                " outline: 0;"
                "}"
                "QTreeWidget#CompletionPopup::item {"
                " padding: 3px 5px;"
                " border: 0;"
                "}"
                "QTreeWidget#CompletionPopup::item:hover {"
                " background-color: %s;"
                "}"
                "QTreeWidget#CompletionPopup::item:selected {"
                " background-color: %s;"
                " color: %s;"
                "}"
            ) % (
                PANEL_BG,
                BORDER_GROUP,
                TEXT_PRIMARY,
                LIST_HOVER_BG,
                SELECTION_BG,
                SELECTION_TEXT,
            )
        )

        self.hide()

    def set_completion_items(
        self,
        items
    ):
        self.clear()

        muted_brush = QtGui.QBrush(
            QtGui.QColor(
                TEXT_MUTED
            )
        )

        for completion in items:
            row = QtGui.QTreeWidgetItem([
                completion.display_text,
                completion.detail,
                completion.label,
            ])
            row.setForeground(
                1,
                muted_brush
            )
            row.setForeground(
                2,
                muted_brush
            )
            self.addTopLevelItem(
                row
            )

        if self.topLevelItemCount():
            self.setCurrentItem(
                self.topLevelItem(
                    0
                )
            )

    def current_row(self):
        item = self.currentItem()
        if item is None:
            return -1
        return self.indexOfTopLevelItem(
            item
        )

    def select_relative(
        self,
        step
    ):
        count = self.topLevelItemCount()
        if not count:
            return

        row = self.current_row()
        if row < 0:
            row = 0
        else:
            row = (
                row + step
            ) % count

        item = self.topLevelItem(
            row
        )
        self.setCurrentItem(
            item
        )
        try:
            self.scrollToItem(
                item,
                QtGui.QAbstractItemView.EnsureVisible
            )
        except Exception:
            pass

    def place_at_cursor(
        self,
        row_count
    ):
        viewport = self.editor.viewport()
        available_width = max(
            160,
            viewport.width() - 8
        )
        width = min(
            520,
            max(
                300,
                available_width
            )
        )

        visible_rows = max(
            1,
            min(
                int(row_count),
                8
            )
        )
        row_height = max(
            22,
            self.editor.fontMetrics().height() + 8
        )
        height = (
            visible_rows * row_height +
            4
        )
        height = min(
            height,
            max(
                row_height + 4,
                viewport.height() - 8
            )
        )

        rect = self.editor.cursorRect()
        x_pos = rect.left()
        y_pos = rect.bottom() + 2

        if x_pos + width > viewport.width():
            x_pos = max(
                4,
                viewport.width() - width - 4
            )

        if y_pos + height > viewport.height():
            y_pos = max(
                4,
                rect.top() - height - 2
            )

        self.setGeometry(
            x_pos,
            y_pos,
            width,
            height
        )

        name_width = int(
            width * 0.48
        )
        kind_width = int(
            width * 0.20
        )
        self.setColumnWidth(
            0,
            name_width
        )
        self.setColumnWidth(
            1,
            kind_width
        )
        self.setColumnWidth(
            2,
            max(
                80,
                width -
                name_width -
                kind_width -
                8
            )
        )


class CompletionController(QtCore.QObject):

    def __init__(
        self,
        editor
    ):
        QtCore.QObject.__init__(
            self,
            editor
        )
        self.editor = editor
        self.popup = CompletionPopup(
            editor
        )
        self.items = []
        self._context = None
        self._committing = False

        self.engine = CompletionEngine([
            EditorItemsProvider(
                self._editor_items
            ),
            ScriptToolboxApiProvider(
                self._toolbox
            ),
        ])

        self.editor.installEventFilter(
            self
        )
        try:
            self.editor.viewport().installEventFilter(
                self
            )
        except Exception:
            pass
        self.editor.textChanged.connect(
            self._text_changed
        )
        self.editor.cursorPositionChanged.connect(
            self._cursor_moved
        )
        try:
            self.editor.updateRequest.connect(
                self._editor_updated
            )
        except Exception:
            pass

        self.popup.itemClicked.connect(
            self._popup_clicked
        )
        self.popup.itemActivated.connect(
            self._popup_activated
        )

    # ------------------------------------------------------------------
    # Context adapters
    # ------------------------------------------------------------------

    def _ancestors(self):
        current = self.editor
        seen = set()

        while current is not None:
            identity = id(current)
            if identity in seen:
                break
            seen.add(identity)
            yield current

            try:
                current = current.parent()
            except Exception:
                current = None

    def _toolbox(self):
        for owner in self._ancestors():
            toolbox = getattr(
                owner,
                "toolbox",
                None
            )
            if toolbox is not None:
                return toolbox
        return None

    def _editor_items(self):
        for owner in self._ancestors():
            working = getattr(
                owner,
                "working",
                None
            )
            if isinstance(
                working,
                dict
            ):
                return list(
                    walk_items(
                        working,
                        include_folders=False
                    )
                )

        toolbox = self._toolbox()
        if toolbox is None:
            return []

        callback = getattr(
            toolbox,
            "all_items",
            None
        )
        if not callable(callback):
            return []

        try:
            return list(
                callback()
            )
        except Exception:
            return []

    def _language(self):
        for owner in self._ancestors():
            callback = getattr(
                owner,
                "language",
                None
            )
            if not callable(callback):
                continue
            try:
                value = text_type(
                    callback() or ""
                ).lower()
            except Exception:
                continue
            if value:
                return value
        return "python"

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def hide(self):
        self.popup.hide()
        self.items = []
        self._context = None

    def _text_changed(self):
        if self._committing:
            return
        self.show(
            manual=False
        )

    def _cursor_moved(self):
        if not self.popup.isVisible():
            return
        self.show(
            manual=False,
            keep_if_empty=False
        )

    def _editor_updated(
        self,
        *args
    ):
        if self.popup.isVisible():
            self.popup.place_at_cursor(
                len(
                    self.items
                )
            )

    def _can_show(
        self,
        manual
    ):
        if self._language() != "python":
            return False
        if manual:
            return True
        try:
            return self.editor.hasFocus()
        except Exception:
            return True

    def show(
        self,
        manual=False,
        keep_if_empty=False
    ):
        if not self._can_show(
            manual
        ):
            self.hide()
            return False

        cursor = self.editor.textCursor()
        text = text_type(
            self.editor.toPlainText()
        )
        position = cursor.position()

        context, items = self.engine.complete(
            text,
            cursor_position=position,
            manual=manual
        )

        if (
            not manual and
            context.kind == CONTEXT_IDENTIFIER and
            not context.prefix
        ):
            self.hide()
            return False

        if (
            not manual and
            context.kind not in (
                CONTEXT_IDENTIFIER,
                CONTEXT_TOOLBOX_MEMBER,
                CONTEXT_ITEM_ARGUMENT,
            )
        ):
            self.hide()
            return False

        if not items:
            if not keep_if_empty:
                self.hide()
            return False

        self.items = items
        self._context = context
        self.popup.set_completion_items(
            items
        )
        self.popup.place_at_cursor(
            len(items)
        )
        self.popup.show()
        self.popup.raise_()
        return True

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def eventFilter(
        self,
        watched,
        event
    ):
        is_editor = watched is self.editor
        is_viewport = False
        try:
            is_viewport = watched is self.editor.viewport()
        except Exception:
            pass

        if not is_editor and not is_viewport:
            return False

        event_type = event.type()

        if event_type == QtCore.QEvent.FocusOut:
            self.hide()
            return False

        if event_type == QtCore.QEvent.MouseButtonPress:
            self.hide()
            return False

        if not is_editor:
            return False

        if event_type != QtCore.QEvent.KeyPress:
            return False

        key = event.key()
        modifiers = event.modifiers()

        if (
            key == QtCore.Qt.Key_Space and
            modifiers & QtCore.Qt.ControlModifier
        ):
            self.show(
                manual=True
            )
            return True

        if not self.popup.isVisible():
            return False

        if key == QtCore.Qt.Key_Escape:
            self.hide()
            return True

        if key == QtCore.Qt.Key_Up:
            self.popup.select_relative(
                -1
            )
            return True

        if key == QtCore.Qt.Key_Down:
            self.popup.select_relative(
                1
            )
            return True

        if key in (
            QtCore.Qt.Key_Return,
            QtCore.Qt.Key_Enter,
            QtCore.Qt.Key_Tab,
        ):
            return self.commit_current()

        return False

    def _popup_clicked(
        self,
        item,
        column
    ):
        self.commit_current()

    def _popup_activated(
        self,
        item,
        column
    ):
        self.commit_current()

    def commit_current(self):
        row = self.popup.current_row()
        if (
            row < 0 or
            row >= len(
                self.items
            )
        ):
            self.hide()
            return False

        completion = self.items[
            row
        ]

        cursor = self.editor.textCursor()
        position = cursor.position()
        text = text_type(
            self.editor.toPlainText()
        )
        context = self.engine.context(
            text,
            cursor_position=position,
            manual=True
        )

        if context.kind not in (
            CONTEXT_IDENTIFIER,
            CONTEXT_TOOLBOX_MEMBER,
            CONTEXT_ITEM_ARGUMENT,
        ):
            self.hide()
            return False

        start = context.start
        end = context.end
        insertion = completion.insert_text

        cursor.beginEditBlock()
        self._committing = True
        try:
            cursor.setPosition(
                start
            )
            cursor.setPosition(
                end,
                QtGui.QTextCursor.KeepAnchor
            )
            cursor.insertText(
                insertion
            )

            if completion.cursor_offset is None:
                target = (
                    start +
                    len(
                        insertion
                    )
                )
            else:
                target = (
                    start +
                    max(
                        0,
                        min(
                            int(
                                completion.cursor_offset
                            ),
                            len(
                                insertion
                            )
                        )
                    )
                )

            cursor.setPosition(
                target
            )
            self.editor.setTextCursor(
                cursor
            )
        finally:
            cursor.endEditBlock()
            self._committing = False

        self.hide()

        if completion.source == SOURCE_TOOLBOX_API:
            new_context = self.engine.context(
                text_type(
                    self.editor.toPlainText()
                ),
                cursor_position=self.editor.textCursor().position(),
                manual=True
            )
            if new_context.kind == CONTEXT_ITEM_ARGUMENT:
                self.show(
                    manual=True
                )

        return True


__all__ = [
    "CompletionController",
    "CompletionPopup",
]
