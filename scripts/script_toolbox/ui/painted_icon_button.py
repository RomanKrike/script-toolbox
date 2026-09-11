# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore
from ..compat import QtGui
from ..style import palette


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
                fill = QtGui.QColor(
                    palette.ICON_BUTTON_PRESSED_BG
                )
                border = QtGui.QColor(
                    palette.BORDER_INSET
                )
            elif self._hovered:
                fill = QtGui.QColor(
                    palette.ICON_BUTTON_HOVER_BG
                )
                border = QtGui.QColor(
                    palette.ICON_BUTTON_HOVER_BORDER
                )
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


__all__ = [
    "PaintedIconButton",
]
