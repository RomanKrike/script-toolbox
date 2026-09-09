# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore
from ..compat import QtGui
from ..pycompat import text_type
from ..style.builtin_icons import builtin_icon


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

        self.search_icon = QtGui.QToolButton(
            self
        )
        self.search_icon.setObjectName(
            "SearchFieldIcon"
        )
        self.search_icon.setAutoRaise(True)
        self.search_icon.setIcon(
            builtin_icon("find")
        )
        self.search_icon.setIconSize(
            QtCore.QSize(12, 12)
        )
        self.search_icon.setFixedSize(
            _SEARCH_ICON_SIZE,
            _SEARCH_ICON_SIZE
        )
        self.search_icon.setFocusPolicy(
            QtCore.Qt.NoFocus
        )
        self.search_icon.setToolTip(
            "Search"
        )
        try:
            self.search_icon.setAttribute(
                QtCore.Qt.WA_TransparentForMouseEvents,
                True
            )
        except Exception:
            pass

        self.clear_button = QtGui.QToolButton(
            self
        )
        self.clear_button.setObjectName(
            "SearchFieldClear"
        )
        self.clear_button.setAutoRaise(True)
        self.clear_button.setIcon(
            builtin_icon("close")
        )
        # Keep extra breathing room around the Solar close glyph. Maya/Qt4
        # can crop the antialiased edge at small odd icon sizes.
        self.clear_button.setIconSize(
            QtCore.QSize(9, 9)
        )
        self.clear_button.setFixedSize(
            _CLEAR_BUTTON_SIZE,
            _CLEAR_BUTTON_SIZE
        )
        self.clear_button.setFocusPolicy(
            QtCore.Qt.NoFocus
        )
        self.clear_button.setToolTip(
            "Clear search"
        )
        self.clear_button.clicked.connect(
            self.clear
        )

        try:
            self.setTextMargins(
                25,
                0,
                28,
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
            4,
            search_top
        )
        self.clear_button.move(
            max(
                4,
                self.width() - _CLEAR_BUTTON_SIZE - 5
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
