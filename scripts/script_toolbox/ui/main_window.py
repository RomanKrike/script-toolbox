# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import HOST
from ..compat import QtCore
from ..compat import QtGui
from ..compat import main_window
from ..compat import shift_pressed
from ..constants import PLUGIN_VERSION
from ..constants import WINDOW_OBJECT_NAME
from ..core.config import load_config
from ..core.config import save_config
from ..core.executor import evaluate_python_state
from ..core.executor import execute_script
from ..core.values import find_item
from ..core.values import get_value as get_document_value
from ..core.values import store_value as store_document_value
from ..model import walk_items
from ..model.items import safe_color
from ..pycompat import text_type
from ..style import STYLE
from ..style import toolbar_icon
from .runtime import build_folder_widgets
from .update_ui import UpdateCheckThread
from .update_ui import UpdateInstallThread


_TOOLBOX = None


class ScriptToolbox(QtGui.QMainWindow):

    def __init__(
        self,
        parent=None
    ):
        QtGui.QMainWindow.__init__(
            self,
            parent or main_window()
        )

        self.setObjectName(
            WINDOW_OBJECT_NAME
        )
        self.setWindowTitle(
            "Script Toolbox {0} - {1}".format(
                PLUGIN_VERSION,
                HOST.display_name
            )
        )
        self.resize(
            420,
            700
        )
        self.setMinimumWidth(
            310
        )
        self.setStyleSheet(
            STYLE
        )

        self.config = load_config()
        self.editor_window = None
        self.field_widgets = {}
        self.state_button_widgets = {}
        self._selection_signature = None
        self._on_change_guard = set()

        self.update_info = None
        self.update_check_thread = None
        self.update_install_thread = None
        self._manual_update_check = False

        self.build_ui()
        self.rebuild()

        self.selection_timer = QtCore.QTimer(
            self
        )
        self.selection_timer.setInterval(
            300
        )
        self.selection_timer.timeout.connect(
            self.refresh_selection_fields
        )
        self.selection_timer.start()

        # Check once per host session/window without blocking the UI thread.
        QtCore.QTimer.singleShot(
            1200,
            self.check_for_updates
        )

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def build_ui(self):
        central = QtGui.QWidget()
        central.setObjectName(
            "ToolboxCentral"
        )
        self.setCentralWidget(
            central
        )

        root = QtGui.QVBoxLayout(
            central
        )
        root.setContentsMargins(
            0,
            0,
            0,
            0
        )
        root.setSpacing(
            0
        )

        topbar = QtGui.QFrame()
        topbar.setObjectName(
            "TopBar"
        )

        top_layout = QtGui.QHBoxLayout(
            topbar
        )
        top_layout.setContentsMargins(
            6,
            4,
            6,
            4
        )
        top_layout.setSpacing(
            4
        )

        title = QtGui.QLabel(
            "SCRIPT TOOLBOX  v{0}  |  {1}".format(
                PLUGIN_VERSION,
                HOST.display_name.upper()
            )
        )
        title.setObjectName(
            "ToolboxTitle"
        )
        title.setToolTip(
            "Script Toolbox {0} - {1}".format(
                PLUGIN_VERSION,
                HOST.display_name
            )
        )

        top_layout.addWidget(
            title
        )
        top_layout.addStretch(
            1
        )

        self.update_button = QtGui.QToolButton()
        self.update_button.setObjectName(
            "UpdateButton"
        )
        self.update_button.setIcon(
            toolbar_icon(
                "update"
            )
        )
        self.update_button.setIconSize(
            QtCore.QSize(
                16,
                16
            )
        )
        self.update_button.setToolButtonStyle(
            QtCore.Qt.ToolButtonTextBesideIcon
        )
        self.update_button.setText(
            "UPDATE"
        )
        self.update_button.setToolTip(
            "Install the latest Script Toolbox release"
        )
        self.update_button.setVisible(
            False
        )
        self.update_button.clicked.connect(
            self.install_available_update
        )

        check_updates_button = QtGui.QToolButton()
        check_updates_button.setObjectName(
            "IconButton"
        )
        check_updates_button.setIcon(
            toolbar_icon(
                "update"
            )
        )
        check_updates_button.setIconSize(
            QtCore.QSize(
                18,
                18
            )
        )
        check_updates_button.setFixedSize(
            28,
            28
        )
        check_updates_button.setToolTip(
            "Check for Script Toolbox updates"
        )
        check_updates_button.clicked.connect(
            self.manual_check_for_updates
        )

        reload_button = QtGui.QToolButton()
        reload_button.setObjectName(
            "IconButton"
        )
        reload_button.setIcon(
            toolbar_icon(
                "reload"
            )
        )
        reload_button.setIconSize(
            QtCore.QSize(
                18,
                18
            )
        )
        reload_button.setFixedSize(
            28,
            28
        )
        reload_button.setToolTip(
            "Reload toolbox config"
        )
        reload_button.clicked.connect(
            self.reload_config
        )

        gear = QtGui.QToolButton()
        gear.setObjectName(
            "IconButton"
        )
        gear.setIcon(
            toolbar_icon(
                "gear"
            )
        )
        gear.setIconSize(
            QtCore.QSize(
                18,
                18
            )
        )
        gear.setFixedSize(
            28,
            28
        )
        gear.setToolTip(
            "Edit Interface"
        )
        gear.clicked.connect(
            self.open_interface_editor
        )

        top_layout.addWidget(
            self.update_button
        )
        top_layout.addWidget(
            check_updates_button
        )
        top_layout.addWidget(
            reload_button
        )
        top_layout.addWidget(
            gear
        )

        root.addWidget(
            topbar
        )

        self.scroll = QtGui.QScrollArea()
        self.scroll.setObjectName(
            "ToolboxScroll"
        )
        self.scroll.setWidgetResizable(
            True
        )

        self.scroll.viewport().setStyleSheet(
            "background-color: #2b2b2b;"
        )

        self.content = QtGui.QWidget()
        self.content.setObjectName(
            "ToolboxContent"
        )

        self.content_layout = QtGui.QVBoxLayout(
            self.content
        )
        self.content_layout.setContentsMargins(
            6,
            6,
            6,
            6
        )
        self.content_layout.setSpacing(
            5
        )
        self.content_layout.addStretch(
            1
        )

        self.scroll.setWidget(
            self.content
        )
        root.addWidget(
            self.scroll,
            1
        )

        self.statusBar().showMessage(
            "{0} | Click = script | Shift+Click = alternate script | Name = script ID".format(
                HOST.display_name
            )
        )

    # ------------------------------------------------------------------
    # Config / value API
    # ------------------------------------------------------------------

    def save(self):
        save_config(
            self.config
        )

    def all_items(self):
        return walk_items(
            self.config,
            include_folders=False
        )

    def find_item(
        self,
        key
    ):
        return find_item(
            self.config,
            key
        )

    def get_value(
        self,
        key,
        default=None
    ):
        return get_document_value(
            self.config,
            key,
            default
        )

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
            self.save()
            self._run_on_change(
                item,
                old_value,
                new_value
            )
            self.refresh_state_buttons()

        return True

    def _run_on_change(
        self,
        item,
        old_value,
        value
    ):
        code = item.get(
            "on_change_script",
            ""
        )
        item_id = text_type(
            item.get("id", "")
        )

        if (
            not code.strip() or
            item_id in self._on_change_guard
        ):
            return True

        self._on_change_guard.add(item_id)
        try:
            return execute_script(
                code,
                "python",
                parent=self,
                toolbox=self,
                extra_namespace={
                    "value": value,
                    "old_value": old_value,
                    "host": HOST,
                }
            )
        finally:
            self._on_change_guard.discard(item_id)

    def set_value(
        self,
        key,
        value
    ):
        item = self.find_item(key)

        if not self.store_value(key, value):
            return False

        if (
            item is not None and
            item.get("kind") == "field"
        ):
            self.refresh_field_widget(
                item["id"]
            )
            return True

        self.rebuild()
        return True

    def set_result(
        self,
        key,
        value
    ):
        return self.set_value(key, value)

    # ------------------------------------------------------------------
    # Field API
    # ------------------------------------------------------------------

    def register_field_widget(
        self,
        item_id,
        widget
    ):
        self.field_widgets[
            text_type(item_id)
        ] = widget

    def field_display_values(
        self,
        key
    ):
        item = self.find_item(key)

        if (
            item is None or
            item.get("kind") != "field"
        ):
            return []

        value = item.get("value", "")

        if value is None:
            return []

        if isinstance(value, (list, tuple)):
            return [
                text_type(entry)
                for entry in value
                if text_type(entry).strip()
            ]

        value = text_type(value or "")

        if item.get("multiple", True):
            normalized = (
                value
                .replace(";", "\n")
                .replace(",", "\n")
            )
            return [
                part.strip()
                for part in normalized.splitlines()
                if part.strip()
            ]

        return [value] if value else []

    def field_display_text(
        self,
        key
    ):
        return ", ".join(
            self.field_display_values(key)
        )

    def refresh_field_widget(
        self,
        key
    ):
        item = self.find_item(key)

        if item is None:
            return

        widget = self.field_widgets.get(
            item["id"]
        )

        if widget is not None:
            try:
                widget.refresh()
            except Exception:
                pass

    def get_field_selection(
        self,
        key
    ):
        item = self.find_item(key)

        if (
            item is None or
            item.get("kind") != "field"
        ):
            return []

        widget = self.field_widgets.get(
            item["id"]
        )

        if widget is not None:
            try:
                return widget.selected_values()
            except Exception:
                pass

        return self.field_display_values(key)

    def add_to_field(
        self,
        key,
        values
    ):
        item = self.find_item(key)

        if (
            item is None or
            item.get("kind") != "field"
        ):
            return False

        if isinstance(values, (list, tuple)):
            incoming = [
                text_type(value)
                for value in values
                if text_type(value).strip()
            ]
        else:
            incoming = [
                text_type(values)
            ] if text_type(values or "").strip() else []

        current = self.field_display_values(key)
        result = list(current)

        for value in incoming:
            if value not in result:
                result.append(value)

        if not item.get("multiple", True):
            result = result[-1:]
            value = result[0] if result else ""
        else:
            value = result

        return self.set_value(key, value)

    def remove_from_field(
        self,
        key,
        values=None
    ):
        item = self.find_item(key)

        if (
            item is None or
            item.get("kind") != "field"
        ):
            return False

        if values is None:
            values = self.get_field_selection(key)

        if isinstance(values, (list, tuple)):
            remove_values = set(
                text_type(value)
                for value in values
            )
        else:
            remove_values = set([
                text_type(values)
            ])

        result = [
            value
            for value in self.field_display_values(key)
            if value not in remove_values
        ]

        if not item.get("multiple", True):
            value = result[0] if result else ""
        else:
            value = result

        return self.set_value(key, value)

    def clear_field(
        self,
        key
    ):
        item = self.find_item(key)
        if (
            item is None or
            item.get("kind") != "field"
        ):
            return False

        return self.set_value(
            key,
            [] if item.get("multiple", True) else ""
        )

    def field_scene_objects(
        self,
        key,
        values=None
    ):
        candidates = (
            self.field_display_values(key)
            if values is None
            else [
                text_type(value)
                for value in values
            ]
        )

        return [
            candidate
            for candidate in candidates
            if HOST.object_exists(candidate)
        ]

    def select_field_objects(
        self,
        key,
        values=None
    ):
        objects = self.field_scene_objects(
            key,
            values=values
        )

        if not objects:
            return False

        return bool(
            HOST.select_objects(objects)
        )

    def refresh_selection_fields(
        self,
        force=False
    ):
        try:
            raw_selection = HOST.current_selection(
                long_names=True
            ) or []
        except Exception:
            raw_selection = []

        signature = tuple(raw_selection)

        if (
            not force and
            signature == self._selection_signature
        ):
            return

        self._selection_signature = signature

        selection_fields = [
            item
            for item in self.all_items()
            if (
                item.get("kind") == "field" and
                item.get("source") == "selection"
            )
        ]

        for item in selection_fields:
            try:
                values = HOST.current_selection(
                    long_names=bool(
                        item.get("long_names", False)
                    )
                ) or []

                if not item.get("multiple", True):
                    values = values[:1]
                    new_value = values[0] if values else ""
                else:
                    new_value = values

                old_value = item.get("value", "")
                item["value"] = new_value
                self.refresh_field_widget(item["id"])

                if old_value != new_value:
                    self._run_on_change(
                        item,
                        old_value,
                        new_value
                    )
            except Exception:
                pass

        self.refresh_state_buttons()

    # ------------------------------------------------------------------
    # Runtime
    # ------------------------------------------------------------------

    def register_state_button(
        self,
        item_id,
        widget
    ):
        self.state_button_widgets[
            text_type(item_id)
        ] = widget

    def refresh_state_button(
        self,
        key
    ):
        item = self.find_item(key)

        if (
            item is None or
            item.get("kind") != "button" or
            item.get("mode", "action") != "state"
        ):
            return False

        widget = self.state_button_widgets.get(
            item["id"]
        )

        if widget is None:
            return False

        state = evaluate_python_state(
            item.get("state_get_script", ""),
            toolbox=self,
            parent=self
        )

        if state is None:
            return None

        label = item.get(
            "state_on_label" if state else "state_off_label",
            item.get("label", item["name"])
        )
        color = safe_color(
            item.get(
                "state_on_color" if state else "state_off_color"
            )
        )
        rgb = [
            int(value * 255)
            for value in color
        ]

        widget.setText(
            text_type(label)
        )
        widget.setProperty(
            "stateOn",
            bool(state)
        )
        widget.setStyleSheet(
            "QPushButton#ScriptButton {"
            "background-color: rgb(%d,%d,%d);"
            "}" % (
                rgb[0],
                rgb[1],
                rgb[2]
            )
        )
        return state

    def refresh_state_buttons(self):
        for item_id in list(
            self.state_button_widgets.keys()
        ):
            try:
                self.refresh_state_button(item_id)
            except Exception:
                pass

    def rebuild(self):
        self.field_widgets = {}
        self.state_button_widgets = {}

        while self.content_layout.count() > 1:
            layout_item = self.content_layout.takeAt(0)
            widget = layout_item.widget()

            if widget is not None:
                widget.deleteLater()

        widgets = build_folder_widgets(
            self,
            self.config["sections"],
            self.content
        )

        for widget in widgets:
            self.content_layout.insertWidget(
                self.content_layout.count() - 1,
                widget
            )

        self.refresh_selection_fields(force=True)
        self.refresh_state_buttons()

    def run_item(
        self,
        item_id
    ):
        item = self.find_item(item_id)

        if (
            not item or
            item.get("kind") != "button"
        ):
            return

        if item.get("mode", "action") == "state":
            state = self.refresh_state_button(
                item["id"]
            )
            if state is None:
                return
            code = item.get(
                "state_off_script" if state else "state_on_script",
                ""
            )
        else:
            code = item.get("click_script", "")

            if (
                shift_pressed() and
                item.get("shift_script", "").strip()
            ):
                code = item.get("shift_script", "")

        success = execute_script(
            code,
            item.get("language", "python"),
            parent=self,
            toolbox=self
        )

        if item.get("mode", "action") == "state":
            self.refresh_state_button(
                item["id"]
            )

        if success:
            self.statusBar().showMessage(
                "Executed: {0}".format(
                    item.get("label", item["name"])
                ),
                2500
            )

    # ------------------------------------------------------------------
    # Updater
    # ------------------------------------------------------------------

    def manual_check_for_updates(self):
        self.check_for_updates(
            manual=True
        )

    def check_for_updates(
        self,
        manual=False
    ):
        if (
            self.update_check_thread is not None and
            self.update_check_thread.isRunning()
        ):
            return

        self._manual_update_check = bool(
            manual
        )

        if manual:
            self.statusBar().showMessage(
                "Checking for Script Toolbox updates..."
            )

        self.update_check_thread = UpdateCheckThread(
            self
        )
        self.update_check_thread.completed.connect(
            self.update_check_finished
        )
        self.update_check_thread.start()

    def update_check_finished(
        self,
        result
    ):
        self.update_info = result

        error = result.get(
            "error"
        )

        if error:
            self.update_button.setVisible(
                False
            )
            self.statusBar().showMessage(
                "Update check failed: {0}".format(
                    error
                ),
                12000
            )
            self._manual_update_check = False
            return

        if not result.get(
            "available",
            False
        ):
            self.update_button.setVisible(
                False
            )

            if self._manual_update_check:
                self.statusBar().showMessage(
                    "Script Toolbox {0} is up to date.".format(
                        PLUGIN_VERSION
                    ),
                    5000
                )

            self._manual_update_check = False
            return

        latest = result.get(
            "latest_version"
        ) or ""

        self.update_button.setText(
            "UPDATE {0}".format(
                latest
            )
        )
        self.update_button.setToolTip(
            "Script Toolbox {0} is available. Current version: {1}".format(
                latest,
                PLUGIN_VERSION
            )
        )
        self.update_button.setVisible(
            True
        )
        self.statusBar().showMessage(
            "Script Toolbox {0} is available.".format(
                latest
            ),
            7000
        )
        self._manual_update_check = False


    def install_available_update(self):
        if not self.update_info:
            return

        release = self.update_info.get(
            "release"
        )

        if not release:
            return

        latest = self.update_info.get(
            "latest_version",
            ""
        )

        answer = QtGui.QMessageBox.question(
            self,
            "Update Script Toolbox",
            (
                "Install Script Toolbox {0}?\n\n"
                "Your toolbox configuration is stored separately and "
                "will not be replaced. Script Toolbox will reload "
                "automatically after the update."
            ).format(
                latest
            ),
            QtGui.QMessageBox.Yes |
            QtGui.QMessageBox.No,
            QtGui.QMessageBox.Yes
        )

        if answer != QtGui.QMessageBox.Yes:
            return

        self.update_button.setEnabled(
            False
        )
        self.update_button.setText(
            "UPDATING..."
        )
        self.statusBar().showMessage(
            "Installing Script Toolbox {0}...".format(
                latest
            )
        )

        self.update_install_thread = UpdateInstallThread(
            release,
            self
        )
        self.update_install_thread.completed.connect(
            self.update_install_finished
        )
        self.update_install_thread.start()

    def update_install_finished(
        self,
        result
    ):
        if not result.get(
            "installed",
            False
        ):
            self.update_button.setEnabled(
                True
            )

            latest = (
                self.update_info.get(
                    "latest_version",
                    ""
                )
                if self.update_info
                else ""
            )

            self.update_button.setText(
                "UPDATE {0}".format(
                    latest
                ).strip()
            )

            QtGui.QMessageBox.critical(
                self,
                "Update Failed",
                result.get(
                    "error",
                    "Unknown update error."
                )
            )
            return

        version = result.get(
            "version",
            ""
        )

        self.update_button.setText(
            "RELOADING..."
        )
        self.update_button.setEnabled(
            False
        )

        self.statusBar().showMessage(
            "Script Toolbox {0} installed. Reloading...".format(
                version
            )
        )

        # The worker emits its result immediately before QThread.run()
        # returns. Wait briefly so the QThread object can be destroyed safely
        # together with the old Toolbox window during hot reload.
        try:
            if self.update_install_thread is not None:
                self.update_install_thread.wait(
                    2000
                )
        except Exception:
            pass

        QtCore.QTimer.singleShot(
            150,
            self.hot_reload_after_update
        )

    def hot_reload_after_update(self):
        try:
            from ..bootstrap import hot_reload_toolbox

            hot_reload_toolbox()

        except Exception as exc:
            self.update_button.setText(
                "RESTART {0}".format(
                    HOST.display_name.upper()
                )
            )
            self.update_button.setEnabled(
                False
            )

            QtGui.QMessageBox.warning(
                self,
                "Update Installed",
                (
                    "The update was installed, but Script Toolbox "
                    "could not reload itself.\n\n"
                    "Restart {0} to load the new version.\n\n"
                    "{1}"
                ).format(
                    HOST.display_name,
                    text_type(
                        exc
                    )
                )
            )


    # ------------------------------------------------------------------
    # Editor / reload
    # ------------------------------------------------------------------

    def open_interface_editor(self):
        try:
            from .interface_editor import InterfaceEditor
        except ImportError:
            QtGui.QMessageBox.information(
                self,
                "Script Toolbox",
                "The modular runtime is active. "
                "The Interface Editor is the next refactor step."
            )
            return

        try:
            if (
                self.editor_window is not None and
                self.editor_window.isVisible()
            ):
                self.editor_window.raise_()
                self.editor_window.activateWindow()
                return
        except Exception:
            pass

        self.editor_window = InterfaceEditor(
            self,
            parent=self
        )
        self.editor_window.show()
        self.editor_window.raise_()
        self.editor_window.activateWindow()

    def reload_config(self):
        self.config = load_config()
        self.rebuild()

        self.statusBar().showMessage(
            "Config reloaded.",
            2500
        )


def close_toolbox():
    global _TOOLBOX

    try:
        if _TOOLBOX is not None:
            _TOOLBOX.close()
            _TOOLBOX.deleteLater()
    except Exception:
        pass

    _TOOLBOX = None


def show():
    global _TOOLBOX

    close_toolbox()

    _TOOLBOX = ScriptToolbox(
        parent=main_window()
    )
    _TOOLBOX.show()
    _TOOLBOX.raise_()
    _TOOLBOX.activateWindow()

    return _TOOLBOX


__all__ = [
    "ScriptToolbox",
    "close_toolbox",
    "show",
]
