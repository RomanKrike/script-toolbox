# -*- coding: utf-8 -*-
from __future__ import print_function

from ...compat import QtCore
from ...compat import QtGui
from ...pycompat import text_type
from ...style.builtin_icons import builtin_icon
from ..painted_icon_button import PaintedIconButton
from . import base as base_module
from . import bindings as bindings_module


_BaseBindingPanel = bindings_module.BindingPanel

# Trigger-tab geometry is a local Maya/Qt4 compatibility contract. These
# values intentionally stay beside the QTabBar implementation instead of
# becoming generic button metrics: the holder/offset exist specifically to
# prevent old host styles from clipping right-side tab glyphs.
_TRIGGER_TAB_PADDING_HORIZONTAL = 7
_TRIGGER_CLOSE_HOLDER_SIZE = (22, 20)
_TRIGGER_CLOSE_BUTTON_SIZE = 18
_TRIGGER_CLOSE_GLYPH_SIZE = 10
_TRIGGER_CLOSE_OFFSET = (2, 1)
_TRIGGER_ADD_BUTTON_SIZE = 16
_TRIGGER_ADD_GLYPH_SIZE = 12
_TRIGGER_ADD_SPACER_WIDTH = 12

_TRIGGER_TAB_STYLE = """
QTabBar::tab {
    padding-left: %(padding)spx;
    padding-right: %(padding)spx;
}
""" % {
    "padding": _TRIGGER_TAB_PADDING_HORIZONTAL,
}


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

    def _remove_trigger_close_button(self, page):
        index = self.tabs.indexOf(page)
        if index < 0:
            return

        bar = self.tabs.tabBar()
        try:
            holder = bar.tabButton(
                index,
                QtGui.QTabBar.RightSide
            )
        except Exception:
            holder = None

        if holder is None:
            return

        try:
            is_trigger_holder = (
                text_type(holder.objectName()) ==
                "TriggerCloseHolder"
            )
        except Exception:
            is_trigger_holder = False

        if not is_trigger_holder:
            return

        try:
            bar.setTabButton(
                index,
                QtGui.QTabBar.RightSide,
                None
            )
        except Exception:
            pass
        try:
            holder.hide()
            holder.deleteLater()
        except Exception:
            pass

    def _install_trigger_close_button(self, page):
        if page not in self.pages:
            return

        index = self.tabs.indexOf(page)
        if index < 0:
            return

        bar = self.tabs.tabBar()
        try:
            existing = bar.tabButton(
                index,
                QtGui.QTabBar.RightSide
            )
        except Exception:
            existing = None

        try:
            existing_is_trigger_holder = (
                existing is not None and
                text_type(existing.objectName()) ==
                "TriggerCloseHolder"
            )
        except Exception:
            existing_is_trigger_holder = False

        # Required primary triggers cannot be removed. Do not render a close
        # affordance that only leads to a rejection dialog.
        if self._required_page(page):
            if existing_is_trigger_holder:
                self._remove_trigger_close_button(page)
            return

        if existing_is_trigger_holder:
            return

        # Maya/Qt4 can crop a QTabBar right-side control by one pixel. Keep the
        # proven holder geometry, but paint the glyph ourselves so QToolButton
        # and host QStyle no longer control its icon rectangle.
        holder = QtGui.QWidget(bar)
        holder.setObjectName(
            "TriggerCloseHolder"
        )
        holder.setFixedSize(
            *_TRIGGER_CLOSE_HOLDER_SIZE
        )

        button = PaintedIconButton(
            builtin_icon("close"),
            _TRIGGER_CLOSE_GLYPH_SIZE,
            parent=holder,
            interactive=True,
            hover_feedback=True
        )
        button.setObjectName(
            "TriggerCloseButton"
        )
        button.setFixedSize(
            _TRIGGER_CLOSE_BUTTON_SIZE,
            _TRIGGER_CLOSE_BUTTON_SIZE
        )
        button.move(
            *_TRIGGER_CLOSE_OFFSET
        )
        button.setToolTip("Remove trigger")
        button.clicked.connect(
            lambda current=page:
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
        button = PaintedIconButton(
            builtin_icon("add"),
            _TRIGGER_ADD_GLYPH_SIZE,
            parent=bar,
            interactive=False,
            hover_feedback=False
        )
        button.setObjectName("TriggerAddButton")
        button.setFixedSize(
            _TRIGGER_ADD_BUTTON_SIZE,
            _TRIGGER_ADD_BUTTON_SIZE
        )
        button.setToolTip("Add trigger")

        # PaintedIconButton makes non-interactive glyphs transparent for mouse
        # events. Input therefore continues to fall through to QTabBar so the
        # whole trailing tab owns hover/press/click behaviour.
        self._add_tab_button = button

    def _install_add_tab_spacer(self, index):
        bar = self.tabs.tabBar()

        if self._add_tab_spacer is not None:
            try:
                self._add_tab_spacer.deleteLater()
            except Exception:
                pass

        spacer = QtGui.QWidget(bar)
        spacer.setFixedSize(
            _TRIGGER_ADD_SPACER_WIDTH,
            1
        )
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
