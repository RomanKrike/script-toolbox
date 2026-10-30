# -*- coding: utf-8 -*-
"""Qt content placed inside host-owned dock and pane containers."""
from __future__ import print_function

from ..compat import QtGui


class ScriptToolboxPanel(QtGui.QWidget):
    """One host container; a duplicate stays inert until the first closes."""

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setObjectName("ScriptToolboxPanelContent")
        layout = QtGui.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.toolbox = None
        self._message = None
        self.ensure_toolbox()

    def _show_message(self, message):
        if self._message is None:
            self._message = QtGui.QLabel(self)
            self._message.setWordWrap(True)
            self.layout().addWidget(self._message)
        self._message.setText(message)
        self._message.show()

    def ensure_toolbox(self):
        """Refill a host container retained after a window/pane transition."""
        from .debounced_main_window import active_toolbox
        from .debounced_main_window import show_in_panel

        if self.toolbox is not None and self.toolbox is active_toolbox():
            return self.toolbox
        self.toolbox = None
        try:
            toolbox = show_in_panel(self)
        except Exception as exc:
            from ..core.logging_utils import get_logger
            get_logger().exception("Could not populate Script Toolbox pane.")
            self._show_message("Script Toolbox could not open: {0}".format(exc))
            return None
        if toolbox is None:
            self._show_message("Script Toolbox is already open in another pane.")
            return None
        if self._message is not None:
            self._message.hide()
        self.layout().addWidget(toolbox)
        self.toolbox = toolbox
        toolbox.show()
        return toolbox

    def showEvent(self, event):
        self.ensure_toolbox()
        QtGui.QWidget.showEvent(self, event)

    def closeEvent(self, event):
        from script_toolbox.ui.debounced_main_window import active_toolbox
        from script_toolbox.ui.debounced_main_window import close_toolbox
        if self.toolbox is not None and active_toolbox() is self.toolbox:
            try:
                close_toolbox()
            except Exception:
                event.ignore()
                return
        QtGui.QWidget.closeEvent(self, event)


__all__ = ["ScriptToolboxPanel"]
