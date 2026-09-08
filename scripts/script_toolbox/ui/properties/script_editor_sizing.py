# -*- coding: utf-8 -*-

from ...compat import QtCore
from ...compat import QtGui
from . import base as base_module
from . import bindings as bindings_module


_INSTALLED = False
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

    for page in getattr(panel, "pages", []):
        editor = getattr(page, "script_editor", None)
        if editor is not None:
            editor.setMinimumHeight(value)
            try:
                editor.updateGeometry()
            except Exception:
                pass

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


def install_expanding_script_editors():
    """Give property script editors a large default and manual resizing.

    Property editors live in a resizable QScrollArea.  The legacy layout kept
    the Triggers group at its sizeHint, so extra dialog height could end up as
    unused space instead of growing the code editor.  Keep property fields
    compact, give trigger scripts a useful default height, and expose a visible
    vertical drag handle so the editor can be resized without resizing the
    entire Interface Editor window.
    """
    global _INSTALLED
    if _INSTALLED:
        return
    _INSTALLED = True

    original_page_init = bindings_module.BindingPage.__init__

    def binding_page_init(self, *args, **kwargs):
        original_page_init(self, *args, **kwargs)

        if self.script_editor is None:
            return

        self.script_editor.setMinimumHeight(
            _preferred_script_editor_height
        )
        try:
            self.script_editor.setSizePolicy(
                QtGui.QSizePolicy.Expanding,
                QtGui.QSizePolicy.Expanding
            )
        except Exception:
            pass

    bindings_module.BindingPage.__init__ = binding_page_init

    panel_class = bindings_module.BindingPanel
    original_panel_init = panel_class.__init__
    original_refresh_empty = panel_class._refresh_empty

    def binding_panel_init(self, *args, **kwargs):
        original_panel_init(self, *args, **kwargs)

        self.script_resize_handle = ScriptEditorResizeHandle(
            self,
            self
        )
        self.script_resize_handle.setVisible(
            bool(getattr(self, "pages", []))
        )

        try:
            layout = self.layout()
            insert_index = max(
                0,
                layout.count() - 1
            )
            layout.insertWidget(
                insert_index,
                self.script_resize_handle
            )
        except Exception:
            pass

    def refresh_empty(self):
        original_refresh_empty(self)
        try:
            self.script_resize_handle.setVisible(
                bool(self.pages)
            )
        except Exception:
            pass

    panel_class.__init__ = binding_panel_init
    panel_class._refresh_empty = refresh_empty

    original_property_init = base_module.PropertyEditorBase.__init__

    def property_editor_init(self, *args, **kwargs):
        original_property_init(self, *args, **kwargs)

        try:
            self.setSizePolicy(
                QtGui.QSizePolicy.Expanding,
                QtGui.QSizePolicy.Expanding
            )
        except Exception:
            pass

        try:
            index = self.root_layout.indexOf(
                self.binding_panel
            )
            if index >= 0:
                self.root_layout.setStretch(
                    index,
                    1
                )
        except Exception:
            pass

        try:
            self.binding_panel.setSizePolicy(
                QtGui.QSizePolicy.Expanding,
                QtGui.QSizePolicy.Expanding
            )
        except Exception:
            pass

    base_module.PropertyEditorBase.__init__ = property_editor_init


__all__ = [
    "ScriptEditorResizeHandle",
    "install_expanding_script_editors",
]
