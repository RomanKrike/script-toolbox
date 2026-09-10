# -*- coding: utf-8 -*-
from __future__ import print_function

import os

from ..compat import QtCore
from ..compat import QtGui
from ..model.items import safe_color
from ..pycompat import text_type
from ..style import palette


_BUTTON_CENTER_MARKER = "_script_toolbox_icon_only_button_centering"
_ICON_FEEDBACK_MARKER = "_script_toolbox_runtime_icon_feedback"

_ICON_FEEDBACK_BASE = (
    "background-color: transparent;"
    "border: 1px solid transparent;"
    "border-radius: 3px;"
    "padding: 3px;"
)
_ICON_FEEDBACK_HOVER = (
    "background-color: %s;"
    "border: 1px solid %s;"
    "border-radius: 3px;"
    "padding: 3px;"
) % (
    palette.ICON_BUTTON_HOVER_BG,
    palette.ICON_BUTTON_HOVER_BORDER
)
_ICON_FEEDBACK_PRESSED = (
    "background-color: %s;"
    "border: 1px solid %s;"
    "border-radius: 3px;"
    "padding: 3px;"
) % (
    palette.ICON_BUTTON_PRESSED_BG,
    palette.BORDER_INSET
)


class CenteredIconPushButton(QtGui.QPushButton):
    """QPushButton that paints its icon at the exact widget center."""

    def __init__(self, parent=None):
        QtGui.QPushButton.__init__(self, "", parent)
        self._centered_icon = QtGui.QIcon()
        self._centered_icon_size = QtCore.QSize(18, 18)

    def setCenteredIcon(self, icon, size):
        self._centered_icon = QtGui.QIcon(icon)
        self._centered_icon_size = QtCore.QSize(size)
        QtGui.QPushButton.setIcon(self, QtGui.QIcon())
        QtGui.QPushButton.setText(self, "")
        self.update()

    def setText(self, value):
        QtGui.QPushButton.setText(self, "")

    def paintEvent(self, event):
        QtGui.QPushButton.paintEvent(self, event)
        if self._centered_icon.isNull():
            return

        width = max(1, self._centered_icon_size.width())
        height = max(1, self._centered_icon_size.height())
        target = QtCore.QRect(
            (self.width() - width) // 2,
            (self.height() - height) // 2,
            width,
            height
        )
        mode = (
            QtGui.QIcon.Disabled
            if not self.isEnabled()
            else QtGui.QIcon.Active
            if self.underMouse()
            else QtGui.QIcon.Normal
        )
        state = QtGui.QIcon.On if self.isDown() else QtGui.QIcon.Off

        painter = QtGui.QPainter(self)
        try:
            self._centered_icon.paint(
                painter,
                target,
                QtCore.Qt.AlignCenter,
                mode,
                state
            )
        except TypeError:
            self._centered_icon.paint(painter, target)
        painter.end()


def _button_should_center_icon(item):
    icon_path = text_type(item.get("icon_path") or "").strip()
    if not icon_path:
        return False
    if bool(item.get("icon_only", False)):
        return True
    if not bool(item.get("show_label", True)):
        return True
    return not bool(text_type(item.get("label") or "").strip())


def _render_centered_icon_button(owner, item):
    button = CenteredIconPushButton()
    button.setObjectName("ScriptButton")
    button.setToolTip(owner._tooltip(item))

    if item.get("kind") == "toggle_button":
        color = item.get("state_off_color")
    else:
        color = item.get("color")
    rgb = [int(value * 255) for value in safe_color(color)]
    button.setStyleSheet(
        "QPushButton#ScriptButton {background-color: rgb(%d,%d,%d);}" % (
            rgb[0],
            rgb[1],
            rgb[2]
        )
    )

    icon_path = os.path.expanduser(
        os.path.expandvars(text_type(item.get("icon_path") or ""))
    )
    icon_size = int(item.get("icon_size", 18))
    if icon_path:
        button.setCenteredIcon(
            QtGui.QIcon(icon_path),
            QtCore.QSize(icon_size, icon_size)
        )

    button.clicked.connect(
        lambda checked=False, item_id=item["id"]:
        owner.toolbox.run_item(item_id)
    )

    if item.get("kind") == "toggle_button":
        owner.toolbox.register_state_button(item["id"], button)
        owner.toolbox.refresh_state_button(item["id"])

    return button


def install_icon_only_button_centering(registry):
    if getattr(registry, _BUTTON_CENTER_MARKER, False):
        return

    for kind in ("button", "toggle_button"):
        original = registry.renderer_for(kind)
        if original is None:
            continue

        def render_button(
            owner,
            item,
            compact=False,
            original_renderer=original
        ):
            if _button_should_center_icon(item):
                return _render_centered_icon_button(owner, item)
            return original_renderer(owner, item, compact=compact)

        registry.register(kind, render_button, replace=True)

    setattr(registry, _BUTTON_CENTER_MARKER, True)


class IconFeedbackFilter(QtCore.QObject):

    def __init__(self, target, parent=None):
        QtCore.QObject.__init__(self, parent)
        self.target = target

    def _set_style(self, style):
        try:
            self.target.setStyleSheet(style)
        except Exception:
            pass

    def eventFilter(self, watched, event):
        event_type = event.type()
        if event_type == QtCore.QEvent.Enter:
            self._set_style(_ICON_FEEDBACK_HOVER)
        elif event_type == QtCore.QEvent.Leave:
            self._set_style(_ICON_FEEDBACK_BASE)
        elif event_type == QtCore.QEvent.MouseButtonPress:
            self._set_style(_ICON_FEEDBACK_PRESSED)
        elif event_type == QtCore.QEvent.MouseButtonRelease:
            self._set_style(_ICON_FEEDBACK_HOVER)
        return False


def _runtime_icon_target(widget):
    candidates = []
    try:
        candidates = widget.findChildren(QtGui.QWidget)
    except Exception:
        pass

    for candidate in candidates:
        if isinstance(candidate, (QtGui.QAbstractButton, QtGui.QLabel)):
            return candidate
    return None


def install_runtime_icon_feedback(registry):
    if getattr(registry, _ICON_FEEDBACK_MARKER, False):
        return

    for kind in ("icon", "toggle_icon"):
        original = registry.renderer_for(kind)
        if original is None:
            continue

        def render_icon(
            owner,
            item,
            compact=False,
            original_renderer=original
        ):
            widget = original_renderer(owner, item, compact=compact)
            if widget is None:
                return widget

            target = _runtime_icon_target(widget)
            if target is None:
                return widget

            try:
                target.setObjectName("RuntimeIconFeedback")
                current_size = target.size()
                if current_size.width() > 0 and current_size.height() > 0:
                    target.setFixedSize(
                        current_size.width() + 6,
                        current_size.height() + 6
                    )
                target.setStyleSheet(_ICON_FEEDBACK_BASE)
                feedback_filter = IconFeedbackFilter(target, parent=target)
                target.installEventFilter(feedback_filter)
                target._script_toolbox_icon_feedback = feedback_filter
            except Exception:
                pass
            return widget

        registry.register(kind, render_icon, replace=True)

    setattr(registry, _ICON_FEEDBACK_MARKER, True)


__all__ = [
    "CenteredIconPushButton",
    "IconFeedbackFilter",
    "install_icon_only_button_centering",
    "install_runtime_icon_feedback",
]
