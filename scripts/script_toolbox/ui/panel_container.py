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
        from .debounced_main_window import show_in_panel
        self.toolbox = show_in_panel(self)
        if self.toolbox is None:
            label = QtGui.QLabel("Script Toolbox is already open in another pane.")
            label.setWordWrap(True)
            layout.addWidget(label)
        else:
            layout.addWidget(self.toolbox)

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
