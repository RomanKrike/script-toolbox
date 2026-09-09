# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore
from ..compat import QtGui
from ..style.builtin_icons import builtin_icon
from . import editor_polish_hooks as polish_module
from .properties.trigger_tabs import TriggerTabBindingPanel


_INSTALL_MARKER = "_script_toolbox_icon_clip_fix_installed"
_SEARCH_ICON_SIZE = 18
_SEARCH_CLEAR_SIZE = 20


class PaintedIconButton(QtGui.QWidget):
    """Small icon control that bypasses QToolButton/QStyle icon geometry."""

    clicked = QtCore.Signal()

    def __init__(
        self,
        icon,
        icon_size,
        parent=None,
        interactive=True,
        hover_feedback=True
    ):
        QtGui.QWidget.__init__(self, parent)
        self._icon = QtGui.QIcon(icon)
        self._icon_size = QtCore.QSize(icon_size, icon_size)
        self._interactive = bool(interactive)
        self._hover_feedback = bool(hover_feedback)
        self._hovered = False
        self._pressed = False

        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setMouseTracking(True)

        if not self._interactive:
            try:
                self.setAttribute(
                    QtCore.Qt.WA_TransparentForMouseEvents,
                    True
                )
            except Exception:
                pass

    def _icon_rect(self):
        width = max(1, self._icon_size.width())
        height = max(1, self._icon_size.height())
        return QtCore.QRect(
            (self.width() - width) // 2,
            (self.height() - height) // 2,
            width,
            height
        )

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        try:
            painter.setRenderHint(
                QtGui.QPainter.Antialiasing,
                True
            )
        except Exception:
            pass

        if self._interactive and self._hover_feedback:
            if self._pressed:
                fill = QtGui.QColor("#272727")
                border = QtGui.QColor("#171717")
            elif self._hovered:
                fill = QtGui.QColor("#404040")
                border = QtGui.QColor("#545454")
            else:
                fill = None
                border = None

            if fill is not None:
                painter.setBrush(fill)
                painter.setPen(QtGui.QPen(border))
                painter.drawRoundedRect(
                    self.rect().adjusted(0, 0, -1, -1),
                    3,
                    3
                )

        if not self._icon.isNull():
            mode = (
                QtGui.QIcon.Disabled
                if not self.isEnabled()
                else QtGui.QIcon.Active
                if self._hovered
                else QtGui.QIcon.Normal
            )
            state = (
                QtGui.QIcon.On
                if self._pressed
                else QtGui.QIcon.Off
            )
            try:
                self._icon.paint(
                    painter,
                    self._icon_rect(),
                    QtCore.Qt.AlignCenter,
                    mode,
                    state
                )
            except TypeError:
                self._icon.paint(
                    painter,
                    self._icon_rect()
                )

        painter.end()

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        QtGui.QWidget.enterEvent(self, event)

    def leaveEvent(self, event):
        self._hovered = False
        self._pressed = False
        self.update()
        QtGui.QWidget.leaveEvent(self, event)

    def mousePressEvent(self, event):
        if not self._interactive:
            event.ignore()
            return
        if event.button() == QtCore.Qt.LeftButton:
            self._pressed = True
            self.update()
            event.accept()
            return
        QtGui.QWidget.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        if not self._interactive:
            event.ignore()
            return

        was_pressed = self._pressed
        self._pressed = False
        self.update()

        if (
            was_pressed and
            event.button() == QtCore.Qt.LeftButton and
            self.rect().contains(event.pos())
        ):
            self.clicked.emit()
            event.accept()
            return

        QtGui.QWidget.mouseReleaseEvent(self, event)


class SearchDecorationFilter(QtCore.QObject):

    def __init__(
        self,
        line_edit,
        search_icon,
        clear_button,
        parent=None
    ):
        QtCore.QObject.__init__(self, parent)
        self.line_edit = line_edit
        self.search_icon = search_icon
        self.clear_button = clear_button

    def position(self):
        search_top = max(
            0,
            (self.line_edit.height() - _SEARCH_ICON_SIZE) // 2
        )
        clear_top = max(
            0,
            (self.line_edit.height() - _SEARCH_CLEAR_SIZE) // 2
        )

        self.search_icon.move(5, search_top)
        self.clear_button.move(
            max(
                5,
                self.line_edit.width() - _SEARCH_CLEAR_SIZE - 7
            ),
            clear_top
        )
        self.search_icon.raise_()
        self.clear_button.raise_()

    def eventFilter(self, watched, event):
        if event.type() in (
            QtCore.QEvent.Resize,
            QtCore.QEvent.Show,
            QtCore.QEvent.LayoutRequest,
        ):
            self.position()
        return False


def _painted_search_control(line_edit, parent=None):
    search_icon = PaintedIconButton(
        builtin_icon("find"),
        12,
        parent=line_edit,
        interactive=False,
        hover_feedback=False
    )
    search_icon.setObjectName("EditorSearchIcon")
    search_icon.setFixedSize(
        _SEARCH_ICON_SIZE,
        _SEARCH_ICON_SIZE
    )
    search_icon.setToolTip("Search")

    clear_button = PaintedIconButton(
        builtin_icon("close"),
        10,
        parent=line_edit,
        interactive=True,
        hover_feedback=True
    )
    clear_button.setObjectName("EditorSearchClear")
    clear_button.setFixedSize(
        _SEARCH_CLEAR_SIZE,
        _SEARCH_CLEAR_SIZE
    )
    clear_button.setToolTip("Clear search")
    clear_button.clicked.connect(line_edit.clear)

    try:
        line_edit.setTextMargins(
            26,
            0,
            30,
            0
        )
    except Exception:
        pass

    decoration_filter = SearchDecorationFilter(
        line_edit,
        search_icon,
        clear_button,
        parent=line_edit
    )
    line_edit.installEventFilter(decoration_filter)

    def update_clear(value):
        clear_button.setVisible(bool(value))
        decoration_filter.position()

    line_edit.textChanged.connect(update_clear)
    line_edit._script_toolbox_search_icon = search_icon
    line_edit._script_toolbox_clear_button = clear_button
    line_edit._script_toolbox_search_filter = decoration_filter

    update_clear(line_edit.text())
    return line_edit


def _install_trigger_close_button(self, page):
    if page not in self.pages:
        return

    index = self.pages.index(page)
    bar = self.tabs.tabBar()

    holder = QtGui.QWidget(bar)
    holder.setObjectName("TriggerCloseHolder")
    holder.setFixedSize(22, 20)

    button = PaintedIconButton(
        builtin_icon("close"),
        10,
        parent=holder,
        interactive=True,
        hover_feedback=True
    )
    button.setObjectName("TriggerCloseButton")
    button.setFixedSize(18, 18)
    button.move(2, 1)
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
        12,
        parent=bar,
        interactive=False,
        hover_feedback=False
    )
    button.setObjectName("TriggerAddButton")
    button.setFixedSize(16, 16)
    button.setToolTip("Add trigger")
    self._add_tab_button = button


def install_icon_clip_fix():
    if getattr(
        polish_module,
        _INSTALL_MARKER,
        False
    ):
        return

    # install_editor_search_ux() calls this module global at widget-build time,
    # so replacing it here affects future InterfaceEditor instances without
    # stacking another build_ui wrapper or leaving stale signal connections.
    polish_module._search_control = _painted_search_control

    # The trigger panel methods are replaced before property editors are
    # instantiated. QTabBar still owns the holder geometry, but QToolButton and
    # QStyle no longer participate in painting the plus/close glyphs.
    TriggerTabBindingPanel._install_trigger_close_button = (
        _install_trigger_close_button
    )
    TriggerTabBindingPanel._ensure_add_button = _ensure_add_button

    setattr(
        polish_module,
        _INSTALL_MARKER,
        True
    )


__all__ = [
    "PaintedIconButton",
    "SearchDecorationFilter",
    "install_icon_clip_fix",
]
