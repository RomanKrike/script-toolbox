# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtGui
from ..pycompat import text_type
from ..style.builtin_icons import builtin_icon
from ..style.metrics import SEARCH_CLEAR_GLYPH_SIZE
from ..style.metrics import SEARCH_CLEAR_RIGHT_OFFSET
from ..style.metrics import SEARCH_CLEAR_SIZE
from ..style.metrics import SEARCH_EDGE_OFFSET
from ..style.metrics import SEARCH_ICON_GLYPH_SIZE
from ..style.metrics import SEARCH_ICON_SIZE
from ..style.metrics import SEARCH_TEXT_MARGIN_LEFT
from ..style.metrics import SEARCH_TEXT_MARGIN_RIGHT
from .painted_icon_button import PaintedIconButton


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
            SEARCH_ICON_GLYPH_SIZE,
            parent=self,
            interactive=False,
            hover_feedback=False
        )
        self.search_icon.setObjectName(
            "SearchFieldIcon"
        )
        self.search_icon.setFixedSize(
            SEARCH_ICON_SIZE,
            SEARCH_ICON_SIZE
        )
        self.search_icon.setToolTip(
            "Search"
        )

        self.clear_button = PaintedIconButton(
            builtin_icon("close"),
            SEARCH_CLEAR_GLYPH_SIZE,
            parent=self,
            interactive=True,
            hover_feedback=True
        )
        self.clear_button.setObjectName(
            "SearchFieldClear"
        )
        self.clear_button.setFixedSize(
            SEARCH_CLEAR_SIZE,
            SEARCH_CLEAR_SIZE
        )
        self.clear_button.setToolTip(
            "Clear search"
        )
        self.clear_button.clicked.connect(
            self.clear
        )

        try:
            self.setTextMargins(
                SEARCH_TEXT_MARGIN_LEFT,
                0,
                SEARCH_TEXT_MARGIN_RIGHT,
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
            (self.height() - SEARCH_ICON_SIZE) // 2
        )
        clear_top = max(
            0,
            (self.height() - SEARCH_CLEAR_SIZE) // 2
        )

        self.search_icon.move(
            SEARCH_EDGE_OFFSET,
            search_top
        )
        self.clear_button.move(
            max(
                SEARCH_EDGE_OFFSET,
                self.width() - SEARCH_CLEAR_SIZE - SEARCH_CLEAR_RIGHT_OFFSET
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
