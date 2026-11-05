# -*- coding: utf-8 -*-
"""Qt content placed inside host-owned dock and pane containers."""
from __future__ import print_function

from ..compat import HOST, QtCore, QtGui
from ..houdini_trace import start_hang_watchdog, trace


def _trace(stage, detail=None):
    if HOST.key == "houdini":
        trace(stage, detail)


class ScriptToolboxPanel(QtGui.QWidget):
    """One host container; a duplicate stays inert until the first closes."""

    def __init__(self, parent=None):
        _trace("container.init_enter")
        QtGui.QWidget.__init__(self, parent)
        _trace("container.qwidget_created")
        self.setObjectName("ScriptToolboxPanelContent")
        layout = QtGui.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.toolbox = None
        self._message = None
        # Hosts adopt this QWidget after construction. Build the Runtime only
        # once the host has shown it; Houdini may create the interface while
        # restoring the desktop, before its Qt pane is ready.
        self._activation_timer = QtCore.QTimer(self)
        self._activation_timer.setSingleShot(True)
        self._activation_timer.timeout.connect(self._activate_toolbox)
        _trace("container.init_done")

    def _activate_toolbox(self):
        _trace("container.activate_enter")
        if self.isVisible():
            _trace("container.ensure_begin")
            self.ensure_toolbox()
            _trace("container.ensure_done")
        else:
            _trace("container.activate_hidden")

    def _show_message(self, message):
        if self._message is None:
            self._message = QtGui.QLabel(self)
            self._message.setWordWrap(True)
            self.layout().addWidget(self._message)
        self._message.setText(message)
        self._message.show()

    def ensure_toolbox(self):
        """Refill a host container retained after a window/pane transition."""
        _trace("container.ensure_enter")
        from .debounced_main_window import active_toolbox
        from .debounced_main_window import show_in_panel

        if self.toolbox is not None and self.toolbox is active_toolbox():
            _trace("container.ensure_existing")
            return self.toolbox
        self.toolbox = None
        try:
            _trace("container.runtime_begin")
            toolbox = show_in_panel(self)
            _trace("container.runtime_returned")
        except Exception as exc:
            from ..core.logging_utils import get_logger
            get_logger().exception("Could not populate Script Toolbox pane.")
            import traceback
            _trace("container.runtime_error", traceback.format_exc())
            self._show_message("Script Toolbox could not open: {0}".format(exc))
            return None
        if toolbox is None:
            _trace("container.runtime_in_other_pane")
            self._show_message("Script Toolbox is already open in another pane.")
            return None
        if self._message is not None:
            self._message.hide()
        self.layout().addWidget(toolbox)
        self.toolbox = toolbox
        _trace("container.toolbox_show_begin")
        toolbox.show()
        _trace("container.toolbox_show_done")
        return toolbox

    def showEvent(self, event):
        _trace("container.show_enter")
        if HOST.key == "houdini":
            start_hang_watchdog(QtCore, QtGui.QApplication.instance())
        self._activation_timer.start(0)
        QtGui.QWidget.showEvent(self, event)
        _trace("container.show_done")

    def closeEvent(self, event):
        _trace("container.close_enter")
        self._activation_timer.stop()
        from script_toolbox.ui.debounced_main_window import active_toolbox
        from script_toolbox.ui.debounced_main_window import close_toolbox
        if self.toolbox is not None and active_toolbox() is self.toolbox:
            try:
                close_toolbox()
            except Exception:
                event.ignore()
                return
        QtGui.QWidget.closeEvent(self, event)
        _trace("container.close_done")


__all__ = ["ScriptToolboxPanel"]
