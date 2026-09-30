# -*- coding: utf-8 -*-

from ...compat import QtCore
from ...compat import QtGui


_DEFAULT_SCRIPT_EDITOR_HEIGHT = 480
_MIN_SCRIPT_EDITOR_HEIGHT = 240
_MAX_SCRIPT_EDITOR_HEIGHT = 1600
_preferred_script_editor_height = _DEFAULT_SCRIPT_EDITOR_HEIGHT


def _clamp_script_editor_height(value):
    return max(
        _MIN_SCRIPT_EDITOR_HEIGHT,
        min(
            _MAX_SCRIPT_EDITOR_HEIGHT,
            int(value)
        )
    )


def _set_panel_script_editor_height(panel, value):
    global _preferred_script_editor_height

    value = _clamp_script_editor_height(value)
    _preferred_script_editor_height = value

    callback = getattr(panel, "script_editor_widgets", None)
    editors = (callback() if callback else
               [getattr(page, "script_editor", None) for page in getattr(panel, "pages", [])])
    for editor in editors:
        if editor is not None:
            editor.setMinimumHeight(value)
            editor.updateGeometry()

    try:
        panel.updateGeometry()
    except Exception:
        pass

    return value


class ScriptEditorResizeHandle(QtGui.QLabel):
    """Visible vertical drag handle for resizing trigger script editors."""

    def __init__(self, panel, parent=None):
        QtGui.QLabel.__init__(
            self,
            "Drag to resize script editor",
            parent
        )
        self.panel = panel
        self._drag_start_y = None
        self._drag_start_height = None

        self.setObjectName("HintText")
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setFixedHeight(16)
        self.setToolTip(
            "Drag vertically to resize the trigger script editor."
        )
        try:
            self.setCursor(
                QtCore.Qt.SizeVerCursor
            )
        except Exception:
            pass

    def mousePressEvent(self, event):
        try:
            if event.button() != QtCore.Qt.LeftButton:
                return QtGui.QLabel.mousePressEvent(
                    self,
                    event
                )
        except Exception:
            pass

        try:
            self._drag_start_y = event.globalY()
        except Exception:
            self._drag_start_y = None

        self._drag_start_height = _preferred_script_editor_height
        try:
            event.accept()
        except Exception:
            pass

    def mouseMoveEvent(self, event):
        if (
            self._drag_start_y is None or
            self._drag_start_height is None
        ):
            return QtGui.QLabel.mouseMoveEvent(
                self,
                event
            )

        try:
            delta = event.globalY() - self._drag_start_y
        except Exception:
            return

        _set_panel_script_editor_height(
            self.panel,
            self._drag_start_height + delta
        )
        try:
            event.accept()
        except Exception:
            pass

    def mouseReleaseEvent(self, event):
        self._drag_start_y = None
        self._drag_start_height = None
        try:
            event.accept()
        except Exception:
            pass


def configure_script_editor(editor):
    editor.setMinimumHeight(_preferred_script_editor_height)
    editor.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)


def configure_binding_panel(panel):
    panel.script_resize_handle = ScriptEditorResizeHandle(panel, panel)
    panel.script_resize_handle.setVisible(bool(panel.pages))
    panel.layout().insertWidget(max(0, panel.layout().count() - 1),
                                panel.script_resize_handle)


def configure_property_editor(editor):
    editor.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
    editor.binding_panel.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
    index = editor.root_layout.indexOf(editor.trigger_section)
    if index >= 0:
        editor.root_layout.setStretch(index, 1)


__all__ = ["ScriptEditorResizeHandle", "configure_script_editor",
           "configure_binding_panel", "configure_property_editor"]
