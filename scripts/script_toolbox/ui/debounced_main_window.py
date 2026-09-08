# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore
from ..compat import QtGui
from ..compat import main_window
from ..core.config_store import ConfigStore
from ..pycompat import text_type
from . import main_window as base_main_window


SAVE_DEBOUNCE_MS = 500


class ScriptToolbox(base_main_window.ScriptToolbox):
    """Runtime window with debounced persistence for value changes.

    Explicit ``save()`` calls remain synchronous. Only saves requested from
    ``store_value()`` are deferred so rapid control events coalesce into one
    atomic config write on the DCC main thread.
    """

    def __init__(
        self,
        parent=None
    ):
        self._defer_config_save = False
        self.config_store = None
        self.save_timer = None

        base_main_window.ScriptToolbox.__init__(
            self,
            parent=parent
        )

        self.config_store = ConfigStore(
            document=self.config
        )

        self.save_timer = QtCore.QTimer(
            self
        )
        self.save_timer.setSingleShot(
            True
        )
        self.save_timer.setInterval(
            SAVE_DEBOUNCE_MS
        )
        self.save_timer.timeout.connect(
            self._flush_scheduled_save
        )

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self):
        if self._defer_config_save:
            return self.schedule_save()

        if self.config_store is None:
            return base_main_window.ScriptToolbox.save(
                self
            )

        if self.save_timer is not None:
            self.save_timer.stop()

        return self.config_store.save(
            self.config
        )

    def schedule_save(self):
        if self.config_store is None:
            return base_main_window.ScriptToolbox.save(
                self
            )

        self.config_store.mark_dirty(
            self.config
        )

        if self.save_timer is not None:
            self.save_timer.start()

        return None

    def _flush_scheduled_save(self):
        try:
            self.flush_pending_save()
        except Exception as exc:
            # Keep ConfigStore dirty so the next explicit save/change/close can
            # retry. Do not raise out of a Qt timer callback in Maya/Nuke.
            try:
                self.statusBar().showMessage(
                    "Config save failed: {0}".format(
                        text_type(exc)
                    ),
                    12000
                )
            except Exception:
                pass

    def flush_pending_save(self):
        if self.save_timer is not None:
            self.save_timer.stop()

        if self.config_store is None:
            return None

        if self.config_store.document is not self.config:
            self.config_store.replace_document(
                self.config,
                dirty=self.config_store.dirty
            )

        return self.config_store.flush()

    def store_value(
        self,
        key,
        value
    ):
        self._defer_config_save = True
        try:
            return base_main_window.ScriptToolbox.store_value(
                self,
                key,
                value
            )
        finally:
            self._defer_config_save = False

    # ------------------------------------------------------------------
    # Lifecycle flush points
    # ------------------------------------------------------------------

    def reload_config(self):
        self.flush_pending_save()

        base_main_window.ScriptToolbox.reload_config(
            self
        )

        self.config_store.replace_document(
            self.config,
            dirty=False
        )

    def install_available_update(self):
        try:
            self.flush_pending_save()
        except Exception as exc:
            QtGui.QMessageBox.critical(
                self,
                "Config Save Failed",
                (
                    "Script Toolbox could not save pending configuration "
                    "changes. The update was not started.\n\n{0}"
                ).format(
                    text_type(exc)
                )
            )
            return

        return base_main_window.ScriptToolbox.install_available_update(
            self
        )

    def hot_reload_after_update(self):
        try:
            self.flush_pending_save()
        except Exception as exc:
            QtGui.QMessageBox.critical(
                self,
                "Config Save Failed",
                (
                    "The update is installed, but pending configuration "
                    "changes could not be saved. Automatic hot reload was "
                    "stopped to avoid losing those changes.\n\n{0}"
                ).format(
                    text_type(exc)
                )
            )
            return

        return base_main_window.ScriptToolbox.hot_reload_after_update(
            self
        )

    def closeEvent(self, event):
        try:
            self.flush_pending_save()
        except Exception as exc:
            QtGui.QMessageBox.critical(
                self,
                "Config Save Failed",
                (
                    "Script Toolbox could not save pending configuration "
                    "changes and will remain open.\n\n{0}"
                ).format(
                    text_type(exc)
                )
            )
            event.ignore()
            return

        QtGui.QMainWindow.closeEvent(
            self,
            event
        )


def close_toolbox():
    toolbox = base_main_window._TOOLBOX

    if toolbox is None:
        return True

    if hasattr(
        toolbox,
        "flush_pending_save"
    ):
        toolbox.flush_pending_save()

    toolbox.close()
    toolbox.deleteLater()
    base_main_window._TOOLBOX = None
    return True


def show():
    close_toolbox()

    toolbox = ScriptToolbox(
        parent=main_window()
    )
    base_main_window._TOOLBOX = toolbox

    toolbox.show()
    toolbox.raise_()
    toolbox.activateWindow()

    return toolbox


__all__ = [
    "SAVE_DEBOUNCE_MS",
    "ScriptToolbox",
    "close_toolbox",
    "show",
]
