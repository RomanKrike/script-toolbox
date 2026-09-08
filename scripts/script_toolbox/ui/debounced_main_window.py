# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import HOST
from ..compat import QtCore
from ..compat import QtGui
from ..compat import main_window
from ..core.config_store import ConfigStore
from ..core.state_refresh import StateRefreshQueue
from ..core.values import store_value as store_document_value
from ..hosts.callbacks import EVENT_SELECTION_CHANGED
from ..hosts.callbacks import HostCallbackGroup
from ..pycompat import text_type
from . import main_window as base_main_window


SAVE_DEBOUNCE_MS = 500
STATE_REFRESH_INTERVAL_MS = 100


class ScriptToolbox(base_main_window.ScriptToolbox):
    """Runtime window with debounced persistence and host event scheduling.

    Explicit ``save()`` calls remain synchronous. Runtime value persistence is
    debounced, full state-button refresh requests are coalesced, and supported
    hosts drive selection fields through normalized callbacks instead of the
    legacy polling timer.
    """

    def __init__(
        self,
        parent=None
    ):
        self.config_store = None
        self.save_timer = None

        self.state_refresh_queue = StateRefreshQueue()
        self.state_refresh_timer = None
        self._selection_refresh_in_progress = False
        self._rebuilding_runtime = False

        self.host_callbacks = HostCallbackGroup(
            HOST
        )
        self._using_selection_callback = False

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

        self.state_refresh_timer = QtCore.QTimer(
            self
        )
        self.state_refresh_timer.setSingleShot(
            True
        )
        self.state_refresh_timer.setInterval(
            STATE_REFRESH_INTERVAL_MS
        )
        self.state_refresh_timer.timeout.connect(
            self._flush_scheduled_state_refresh
        )

        self._install_host_callbacks()

    # ------------------------------------------------------------------
    # Host callbacks
    # ------------------------------------------------------------------

    def _install_host_callbacks(self):
        subscribed = self.host_callbacks.subscribe(
            EVENT_SELECTION_CHANGED,
            self._host_selection_changed
        )

        if not subscribed:
            return False

        self._using_selection_callback = True

        if self.selection_timer is not None:
            self.selection_timer.stop()

        self.refresh_selection_fields(
            force=True
        )
        return True

    def _host_selection_changed(self):
        try:
            self.refresh_selection_fields(
                force=False
            )
        except Exception:
            # Host callbacks must never leak exceptions into Maya/Nuke event
            # dispatch. Polling fallback remains available when subscription
            # cannot be established in the first place.
            pass

    def clear_host_callbacks(self):
        removed = self.host_callbacks.clear()
        self._using_selection_callback = False
        return removed

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self):
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
        item = self.find_item(key)
        old_value = self.get_value(key)

        item = store_document_value(
            self.config,
            key,
            value
        )

        if item is None:
            return False

        new_value = self.get_value(key)

        if old_value != new_value:
            self.schedule_save()
            self._run_on_change(
                item,
                old_value,
                new_value
            )
            self.request_state_refresh()

        return True

    # ------------------------------------------------------------------
    # State refresh scheduling
    # ------------------------------------------------------------------

    def request_state_refresh(self):
        """Request one bounded full refresh without restarting its timer."""
        if not self.state_button_widgets:
            return False

        should_schedule = self.state_refresh_queue.request()

        if not should_schedule:
            return False

        if self.state_refresh_timer is None:
            self.state_refresh_queue.consume()
            base_main_window.ScriptToolbox.refresh_state_buttons(
                self
            )
            return True

        self.state_refresh_timer.start()
        return True

    def _flush_scheduled_state_refresh(self):
        if not self.state_refresh_queue.consume():
            return False

        base_main_window.ScriptToolbox.refresh_state_buttons(
            self
        )
        return True

    def cancel_scheduled_state_refresh(self):
        if self.state_refresh_timer is not None:
            self.state_refresh_timer.stop()

        return self.state_refresh_queue.cancel()

    def refresh_state_buttons(self):
        # Selection events are high-frequency producers, so their request is
        # scheduled unless it is part of a runtime rebuild. Rebuild performs
        # one explicit immediate refresh after all widgets have been created.
        if self._selection_refresh_in_progress:
            if self._rebuilding_runtime:
                return None

            self.request_state_refresh()
            return None

        # Explicit callers retain the old synchronous semantics and also clear
        # a pending scheduled refresh to avoid a duplicate full pass.
        self.cancel_scheduled_state_refresh()
        return base_main_window.ScriptToolbox.refresh_state_buttons(
            self
        )

    def refresh_selection_fields(
        self,
        force=False
    ):
        self._selection_refresh_in_progress = True
        try:
            return base_main_window.ScriptToolbox.refresh_selection_fields(
                self,
                force=force
            )
        finally:
            self._selection_refresh_in_progress = False

    def rebuild(self):
        self._rebuilding_runtime = True
        try:
            return base_main_window.ScriptToolbox.rebuild(
                self
            )
        finally:
            self._rebuilding_runtime = False

    # ------------------------------------------------------------------
    # Lifecycle flush points
    # ------------------------------------------------------------------

    def reload_config(self):
        self.flush_pending_save()
        self.cancel_scheduled_state_refresh()

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

        self.cancel_scheduled_state_refresh()
        self.clear_host_callbacks()

        if self.selection_timer is not None:
            self.selection_timer.stop()

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
    "STATE_REFRESH_INTERVAL_MS",
    "ScriptToolbox",
    "close_toolbox",
    "show",
]
