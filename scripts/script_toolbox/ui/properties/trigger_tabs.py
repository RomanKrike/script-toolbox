# -*- coding: utf-8 -*-
from __future__ import print_function

from ...compat import QtCore
from ...compat import QtGui
from ...pycompat import text_type
from ...style import palette
from ...style.builtin_icons import builtin_icon
from . import base as base_module
from . import bindings as bindings_module


_BaseBindingPanel = bindings_module.BindingPanel

_TRIGGER_TAB_STYLE = """
QTabBar::tab {
    padding-left: 7px;
    padding-right: 7px;
}
QToolButton#TriggerCloseButton,
QToolButton#TriggerAddButton {
    background-color: transparent;
    border: 0px;
    padding: 0px;
}
QToolButton#TriggerCloseButton:hover {
    background-color: %(ICON_BUTTON_HOVER_BG)s;
    border: 1px solid %(ICON_BUTTON_HOVER_BORDER)s;
    border-radius: 3px;
}
QToolButton#TriggerCloseButton:pressed {
    background-color: %(ICON_BUTTON_PRESSED_BG)s;
    border: 1px solid %(BORDER_INSET)s;
    border-radius: 3px;
}
""" % vars(palette)


class TriggerTabBindingPanel(_BaseBindingPanel):
    """Binding panel whose add action is a compact trailing tab."""

    def __init__(
        self,
        toolbox=None,
        parent=None
    ):
        self._add_tab_page = None
        self._add_tab_spacer = None
        self._add_tab_button = None
        _BaseBindingPanel.__init__(
            self,
            toolbox=toolbox,
            parent=parent
        )

        self.tabs.setTabsClosable(False)
        bar = self.tabs.tabBar()
        try:
            bar.setStyleSheet(
                text_type(bar.styleSheet()) +
                "\n" +
                _TRIGGER_TAB_STYLE
            )
        except Exception:
            bar.setStyleSheet(
                _TRIGGER_TAB_STYLE
            )

        try:
            self.tabs.setCornerWidget(
                None,
                QtCore.Qt.TopRightCorner
            )
        except Exception:
            pass

        try:
            self.add_button.hide()
            self.add_button.deleteLater()
        except Exception:
            pass
        self.add_button = None

        self._ensure_add_tab()

    def _hide_add_tab_close_button(self, index):
        bar = self.tabs.tabBar()
        for side in (
            QtGui.QTabBar.LeftSide,
            QtGui.QTabBar.RightSide,
        ):
            try:
                button = bar.tabButton(
                    index,
                    side
                )
                if button is not None:
                    button.hide()
                    button.deleteLater()
                bar.setTabButton(
                    index,
                    side,
                    None
                )
            except Exception:
                pass

    def _install_trigger_close_button(self, page):
        if page not in self.pages:
            return

        index = self.pages.index(page)
        bar = self.tabs.tabBar()

        # QTabBar can crop a right-side tool button by one pixel under older
        # Maya/Qt styles. Give the close control its own holder so the glyph
        # always has real space on both sides instead of touching tab chrome.
        holder = QtGui.QWidget(bar)
        holder.setObjectName(
            "TriggerCloseHolder"
        )
        holder.setFixedSize(20, 18)

        button = QtGui.QToolButton(holder)
        button.setObjectName(
            "TriggerCloseButton"
        )
        button.setAutoRaise(True)
        button.setIcon(
            builtin_icon("close")
        )
        button.setIconSize(
            QtCore.QSize(10, 10)
        )
        button.setFixedSize(16, 16)
        button.move(2, 1)
        button.setFocusPolicy(
            QtCore.Qt.NoFocus
        )
        button.setToolTip("Remove trigger")
        button.setStyleSheet(
            _TRIGGER_TAB_STYLE
        )
        button.clicked.connect(
            lambda checked=False, current=page:
            self.remove_binding(current)
        )

        try:
            bar.setTabButton(
                index,
                QtGui.QTabBar.RightSide,
                holder
            )
        except Exception:
            holder.deleteLater()

    def _ensure_add_button(self):
        if self._add_tab_button is not None:
            return

        bar = self.tabs.tabBar()
        button = QtGui.QToolButton(bar)
        button.setObjectName("TriggerAddButton")
        button.setAutoRaise(True)
        button.setIcon(
            builtin_icon("add")
        )
        button.setIconSize(
            QtCore.QSize(12, 12)
        )
        button.setFixedSize(16, 16)
        button.setFocusPolicy(
            QtCore.Qt.NoFocus
        )
        button.setToolTip("Add trigger")
        button.setStyleSheet(
            _TRIGGER_TAB_STYLE
        )

        # The plus is only a glyph. Mouse input falls through to QTabBar so
        # the normal add-tab hover/pressed feedback is the only indication.
        try:
            button.setAttribute(
                QtCore.Qt.WA_TransparentForMouseEvents,
                True
            )
        except Exception:
            pass

        self._add_tab_button = button

    def _install_add_tab_spacer(self, index):
        bar = self.tabs.tabBar()

        if self._add_tab_spacer is not None:
            try:
                self._add_tab_spacer.deleteLater()
            except Exception:
                pass

        spacer = QtGui.QWidget(bar)
        spacer.setFixedSize(12, 1)
        try:
            spacer.setAttribute(
                QtCore.Qt.WA_TransparentForMouseEvents,
                True
            )
        except Exception:
            pass

        bar.setTabButton(
            index,
            QtGui.QTabBar.LeftSide,
            spacer
        )
        self._add_tab_spacer = spacer

    def _position_add_button(self):
        if (
            self._add_tab_page is None or
            self._add_tab_button is None
        ):
            return

        bar = self.tabs.tabBar()
        index = self.tabs.indexOf(
            self._add_tab_page
        )
        if index < 0:
            self._add_tab_button.hide()
            return

        rect = bar.tabRect(index)
        size = self._add_tab_button.size()
        x_pos = rect.x() + max(
            0,
            (rect.width() - size.width()) // 2
        )
        y_pos = rect.y() + max(
            0,
            (rect.height() - size.height()) // 2
        )
        self._add_tab_button.move(
            x_pos,
            y_pos
        )
        self._add_tab_button.show()
        self._add_tab_button.raise_()

    def _ensure_add_tab(self):
        if self._add_tab_page is None:
            self._add_tab_page = QtGui.QWidget(
                self.tabs
            )
            self._add_tab_page.setObjectName(
                "AddTriggerTabPage"
            )

        index = self.tabs.indexOf(
            self._add_tab_page
        )
        if index < 0:
            index = self.tabs.addTab(
                self._add_tab_page,
                ""
            )

        self.tabs.setTabToolTip(
            index,
            "Add trigger"
        )
        self._hide_add_tab_close_button(
            index
        )
        self._install_add_tab_spacer(
            index
        )
        self._ensure_add_button()
        QtCore.QTimer.singleShot(
            0,
            self._position_add_button
        )

    def _remove_add_tab(self):
        if self._add_tab_button is not None:
            self._add_tab_button.hide()

        if self._add_tab_page is None:
            return

        index = self.tabs.indexOf(
            self._add_tab_page
        )
        if index >= 0:
            self.tabs.removeTab(
                index
            )

    def clear(self):
        if self._add_tab_button is not None:
            self._add_tab_button.hide()
        _BaseBindingPanel.clear(
            self
        )
        self._add_tab_page = None
        self._add_tab_spacer = None
        self._ensure_add_tab()

    def _add_page(self, binding):
        self._remove_add_tab()
        try:
            page = _BaseBindingPanel._add_page(
                self,
                binding
            )
            self._install_trigger_close_button(
                page
            )
            return page
        finally:
            self._ensure_add_tab()

    def eventFilter(self, watched, event):
        if watched is self.tabs.tabBar():
            event_type = event.type()

            if event_type in (
                QtCore.QEvent.Resize,
                QtCore.QEvent.Show,
                QtCore.QEvent.LayoutRequest,
            ):
                QtCore.QTimer.singleShot(
                    0,
                    self._position_add_button
                )

            if event_type == QtCore.QEvent.MouseButtonPress:
                index = watched.tabAt(
                    event.pos()
                )
                add_index = len(
                    self.pages
                )

                if index == add_index:
                    try:
                        if event.button() != QtCore.Qt.LeftButton:
                            return True
                    except Exception:
                        pass

                    QtCore.QTimer.singleShot(
                        0,
                        self.add_binding
                    )
                    return True

        return _BaseBindingPanel.eventFilter(
            self,
            watched,
            event
        )


def install_integrated_trigger_tabs():
    """Route PropertyEditorBase to the integrated trigger-tab panel."""
    bindings_module.BindingPanel = TriggerTabBindingPanel
    base_module.BindingPanel = TriggerTabBindingPanel


__all__ = [
    "TriggerTabBindingPanel",
    "install_integrated_trigger_tabs",
]
