# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtGui
from ..pycompat import text_type
from ..style.builtin_icons import builtin_icon
from .painted_icon_button import PaintedIconButton


_SEARCH_ICON_SIZE = 18
_CLEAR_BUTTON_SIZE = 20


class SearchField(QtGui.QLineEdit):
    """Reusable search line edit with embedded search and clear controls."""

    def __init__(
        self,
        placeholder="",
        parent=None
    ):
        QtGui.QLineEdit.__init__(
            self,
            parent
        )
        self.setObjectName(
            "SearchField"
        )

        try:
            self.setPlaceholderText(
                placeholder
            )
        except Exception:
            pass

        # PaintedIconButton deliberately bypasses QToolButton/QStyle icon
        # geometry. This preserves the Maya 2015 / Qt4 clipping workaround
        # while keeping the search control self-contained.
        self.search_icon = PaintedIconButton(
            builtin_icon("find"),
            12,
            parent=self,
            interactive=False,
            hover_feedback=False
        )
        self.search_icon.setObjectName(
            "SearchFieldIcon"
        )
        self.search_icon.setFixedSize(
            _SEARCH_ICON_SIZE,
            _SEARCH_ICON_SIZE
        )
        self.search_icon.setToolTip(
            "Search"
        )

        self.clear_button = PaintedIconButton(
            builtin_icon("close"),
            10,
            parent=self,
            interactive=True,
            hover_feedback=True
        )
        self.clear_button.setObjectName(
            "SearchFieldClear"
        )
        self.clear_button.setFixedSize(
            _CLEAR_BUTTON_SIZE,
            _CLEAR_BUTTON_SIZE
        )
        self.clear_button.setToolTip(
            "Clear search"
        )
        self.clear_button.clicked.connect(
            self.clear
        )

        try:
            self.setTextMargins(
                26,
                0,
                30,
                0
            )
        except Exception:
            pass

        self.textChanged.connect(
            self._update_clear_button
        )
        self._update_clear_button(
            self.text()
        )

    def _position_buttons(self):
        search_top = max(
            0,
            (self.height() - _SEARCH_ICON_SIZE) // 2
        )
        clear_top = max(
            0,
            (self.height() - _CLEAR_BUTTON_SIZE) // 2
        )

        self.search_icon.move(
            5,
            search_top
        )
        self.clear_button.move(
            max(
                5,
                self.width() - _CLEAR_BUTTON_SIZE - 7
            ),
            clear_top
        )

        try:
            self.search_icon.raise_()
            self.clear_button.raise_()
        except Exception:
            pass

    def _update_clear_button(self, value):
        self.clear_button.setVisible(
            bool(text_type(value or ""))
        )
        self._position_buttons()

    def resizeEvent(self, event):
        QtGui.QLineEdit.resizeEvent(
            self,
            event
        )
        self._position_buttons()

    def showEvent(self, event):
        QtGui.QLineEdit.showEvent(
            self,
            event
        )
        self._position_buttons()


__all__ = [
    "SearchField",
]
