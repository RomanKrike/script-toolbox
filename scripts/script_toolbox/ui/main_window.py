# -*- coding: utf-8 -*-
from __future__ import print_function

import os

from ..compat import HOST
from ..compat import QtCore
from ..compat import QtGui
from ..compat import main_window
from ..constants import PLUGIN_VERSION
from ..constants import WINDOW_OBJECT_NAME
from ..core.config import load_config
from ..core.config import save_config
from ..core.event_bindings import dispatch_item_event
from ..core.executor import evaluate_python_state
from ..core.executor import execute_script_result
from ..core.values import find_item
from ..core.values import get_value as get_document_value
from ..core.values import store_value as store_document_value
from ..model import walk_items
from ..model.items import safe_color
from ..pycompat import text_type
from ..style import STYLE
from ..style import metrics
from ..style import toolbar_icon
from ..style.palette import CONTENT_BG
from .icon_button import ICON_BUTTON_HEADER
from .icon_button import create_icon_button
from .layout_helpers import configure_layout
from .runtime import build_folder_widgets
from .update_ui import UpdateCheckThread
from .update_ui import UpdateInstallThread


_TOOLBOX = None


class ScriptToolbox(QtGui.QMainWindow):

    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent or main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)
        self.setWindowTitle(
            "Script Toolbox {0} - {1}".format(
                PLUGIN_VERSION,
                HOST.display_name
            )
        )
        self.resize(420, 700)
        self.setMinimumWidth(310)
        self.setStyleSheet(STYLE)

        self.config = load_config()
        self.editor_window = None
        self.field_widgets = {}
        self.state_button_widgets = {}
        self.toggle_icon_widgets = {}
        self._selection_signature = None
        self._binding_guard = set()
        self._binding_widget_click_suppression = set()

        self.update_info = None
        self.update_check_thread = None
        self.update_install_thread = None
        self._manual_update_check = False

        self.build_ui()
        self.rebuild()

        self.selection_timer = QtCore.QTimer(self)
        self.selection_timer.setInterval(300)
        self.selection_timer.timeout.connect(self.refresh_selection_fields)
        self.selection_timer.start()

        QtCore.QTimer.singleShot(1200, self.check_for_updates)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def build_ui(self):
        central = QtGui.QWidget()
        central.setObjectName("ToolboxCentral")
        self.setCentralWidget(central)

        root = QtGui.QVBoxLayout(central)
        configure_layout(
            root,
            margins=metrics.MARGINS_NONE,
            spacing=0
        )

        topbar = QtGui.QFrame()
        topbar.setObjectName("TopBar")
        top_layout = QtGui.QHBoxLayout(topbar)
        configure_layout(
            top_layout,
            margins=metrics.TOOLBOX_TOPBAR_MARGINS,
            spacing=metrics.TOOLBOX_TOPBAR_SPACING
        )

        title = QtGui.QLabel(
            "SCRIPT TOOLBOX  v{0}  |  {1}".format(
                PLUGIN_VERSION,
                HOST.display_name.upper()
            )
        )
        title.setObjectName("ToolboxTitle")
        title.setToolTip(
            "Script Toolbox {0} - {1}".format(
                PLUGIN_VERSION,
                HOST.display_name
            )
        )
        top_layout.addWidget(title)
        top_layout.addStretch(1)

        self.update_button = QtGui.QToolButton()
        self.update_button.setObjectName("UpdateButton")
        self.update_button.setIcon(toolbar_icon("update"))
        self.update_button.setIconSize(QtCore.QSize(16, 16))
        self.update_button.setToolButtonStyle(
            QtCore.Qt.ToolButtonTextBesideIcon
        )
        self.update_button.setText("UPDATE")
        self.update_button.setToolTip(
            "Install the latest Script Toolbox release"
        )
        self.update_button.setVisible(False)
        self.update_button.clicked.connect(self.install_available_update)

        self.check_updates_button = create_icon_button(
            "update",
            "Check for Script Toolbox updates",
            self.manual_check_for_updates,
            parent=self,
            preset=ICON_BUTTON_HEADER
        )
        self.reload_button = create_icon_button(
            "reload",
            "Reload toolbox config",
            self.reload_config,
            parent=self,
            preset=ICON_BUTTON_HEADER
        )
        self.interface_editor_button = create_icon_button(
            "gear",
            "Edit Interface",
            self.open_interface_editor,
            parent=self,
            preset=ICON_BUTTON_HEADER
        )

        top_layout.addWidget(self.update_button)
        top_layout.addWidget(self.check_updates_button)
        top_layout.addWidget(self.reload_button)
        top_layout.addWidget(self.interface_editor_button)
        root.addWidget(topbar)

        self.scroll = QtGui.QScrollArea()
        self.scroll.setObjectName("ToolboxScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.viewport().setStyleSheet(
            "background-color: {0};".format(CONTENT_BG)
        )

        self.content = QtGui.QWidget()
        self.content.setObjectName("ToolboxContent")
        self.content_layout = QtGui.QVBoxLayout(self.content)
        configure_layout(
            self.content_layout,
            margins=metrics.TOOLBOX_CONTENT_MARGINS,
            spacing=metrics.TOOLBOX_CONTENT_SPACING
        )
        self.content_layout.addStretch(1)

        self.scroll.setWidget(self.content)
        root.addWidget(self.scroll, 1)
        self.statusBar().showMessage(
            "{0} | Event bindings | ID/name = script identity".format(
                HOST.display_name
            )
        )

    # ------------------------------------------------------------------
    # Config / value API
    # ------------------------------------------------------------------

    def save(self):
        save_config(self.config)

    def all_items(self):
        return walk_items(self.config, include_folders=False)

    def find_item(self, key):
        return find_item(self.config, key)

    def get_value(self, key, default=None):
        return get_document_value(self.config, key, default)

    def dispatch_binding_event(
        self,
        item_or_id,
        event,
        value=None,
        old_value=None,
        mouse_button=None,
        modifiers=None
    ):
        results = dispatch_item_event(
            self,
            item_or_id,
            event,
            value=value,
            old_value=old_value,
            mouse_button=mouse_button,
            modifiers=modifiers,
            parent=self
        )

        if any(
            getattr(result, "success", False)
            for result in results
            if result is not None
        ):
            item = (
                item_or_id
                if isinstance(item_or_id, dict)
                else self.find_item(item_or_id)
            )
            if item is not None:
                self.statusBar().showMessage(
                    "Executed: {0}".format(
                        item.get("label", item.get("name", "Item"))
                    ),
                    2500
                )
        return results

    def _run_on_change(self, item, old_value, value):
        results = self.dispatch_binding_event(
            item,
            "value_changed",
            value=value,
            old_value=old_value
        )
        concrete = [
            result
            for result in results
            if result is not None
        ]
        if not concrete:
            return True
        return all(
            getattr(result, "success", False)
            for result in concrete
        )

    def store_value(self, key, value):
        item = self.find_item(key)
        old_value = self.get_value(key)
        item = store_document_value(self.config, key, value)

        if item is None:
            return False

        new_value = self.get_value(key)
        if old_value != new_value:
            self.save()
            self._run_on_change(item, old_value, new_value)
            self.refresh_state_buttons()
        return True

    def set_value(self, key, value):
        item = self.find_item(key)
        if not self.store_value(key, value):
            return False

        if item is not None and item.get("kind") == "field":
            self.refresh_field_widget(item["id"])
            return True

        self.rebuild()
        return True

    def set_result(self, key, value):
        return self.set_value(key, value)

    # ------------------------------------------------------------------
    # Field API
    # ------------------------------------------------------------------

    def register_field_widget(self, item_id, widget):
        self.field_widgets[text_type(item_id)] = widget

    def field_display_values(self, key):
        item = self.find_item(key)
        if item is None or item.get("kind") != "field":
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
            normalized = value.replace(";", "\n").replace(",", "\n")
            return [
                part.strip()
                for part in normalized.splitlines()
                if part.strip()
            ]
        return [value] if value else []

    def field_display_text(self, key):
        return ", ".join(self.field_display_values(key))

    def refresh_field_widget(self, key):
        item = self.find_item(key)
        if item is None:
            return

        widget = self.field_widgets.get(item["id"])
        if widget is not None:
            try:
                widget.refresh()
            except Exception:
                pass

    def get_field_selection(self, key):
        item = self.find_item(key)
        if item is None or item.get("kind") != "field":
            return []

        widget = self.field_widgets.get(item["id"])
        if widget is not None:
            try:
                return widget.selected_values()
            except Exception:
                pass
        return self.field_display_values(key)

    def add_to_field(self, key, values):
        item = self.find_item(key)
        if item is None or item.get("kind") != "field":
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

        result = list(self.field_display_values(key))
        for value in incoming:
            if value not in result:
                result.append(value)

        if not item.get("multiple", True):
            result = result[-1:]
            value = result[0] if result else ""
        else:
            value = result
        return self.set_value(key, value)

    def remove_from_field(self, key, values=None):
        item = self.find_item(key)
        if item is None or item.get("kind") != "field":
            return False

        if values is None:
            values = self.get_field_selection(key)

        if isinstance(values, (list, tuple)):
            remove_values = set(text_type(value) for value in values)
        else:
            remove_values = set([text_type(values)])

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

    def clear_field(self, key):
        item = self.find_item(key)
        if item is None or item.get("kind") != "field":
            return False
        return self.set_value(
            key,
            [] if item.get("multiple", True) else ""
        )

    def field_scene_objects(self, key, values=None):
        candidates = (
            self.field_display_values(key)
            if values is None
            else [text_type(value) for value in values]
        )
        return [
            candidate
            for candidate in candidates
            if HOST.object_exists(candidate)
        ]

    def select_field_objects(self, key, values=None):
        objects = self.field_scene_objects(key, values=values)
        if not objects:
            return False
        return bool(HOST.select_objects(objects))

    def refresh_selection_fields(self, force=False):
        try:
            raw_selection = HOST.current_selection(long_names=True) or []
        except Exception:
            raw_selection = []

        signature = tuple(raw_selection)
        if not force and signature == self._selection_signature:
            return
        self._selection_signature = signature

        selection_fields = [
            item
            for item in self.all_items()
            if item.get("kind") == "field" and item.get("source") == "selection"
        ]

        for item in selection_fields:
            try:
                values = HOST.current_selection(
                    long_names=bool(item.get("long_names", False))
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
                    self._run_on_change(item, old_value, new_value)
            except Exception:
                pass

        self.refresh_state_buttons()

    # ------------------------------------------------------------------
    # Stateful item API
    # ------------------------------------------------------------------

    def register_state_button(self, item_id, widget):
        self.state_button_widgets[text_type(item_id)] = widget

    def register_toggle_icon(self, item_id, widget):
        self.toggle_icon_widgets[text_type(item_id)] = widget

    def _state_value(self, item):
        if item.get("state_source", "internal") == "script":
            return evaluate_python_state(
                item.get("state_get_script", ""),
                toolbox=self,
                parent=self
            )
        return bool(item.get("value", False))

    def refresh_state_button(self, key):
        item = self.find_item(key)
        if item is None or item.get("kind") != "toggle_button":
            return False

        widget = self.state_button_widgets.get(item["id"])
        if widget is None:
            return False

        state = self._state_value(item)
        if state is None:
            return None

        label = item.get(
            "state_on_label" if state else "state_off_label",
            item.get("label", item.get("name", "Toggle"))
        )
        color = safe_color(
            item.get("state_on_color" if state else "state_off_color")
        )
        rgb = [int(value * 255) for value in color]

        widget.setText("" if item.get("icon_only", False) else text_type(label))
        widget.setProperty("stateOn", bool(state))
        widget.setStyleSheet(
            "QPushButton#ScriptButton {background-color: rgb(%d,%d,%d);}" % (
                rgb[0],
                rgb[1],
                rgb[2]
            )
        )
        return bool(state)

    def _toggle_icon_path(self, item, state):
        return os.path.expanduser(
            os.path.expandvars(
                text_type(
                    item.get(
                        "state_on_path" if state else "state_off_path",
                        ""
                    ) or ""
                )
            )
        )

    def refresh_toggle_icon(self, key):
        item = self.find_item(key)
        if item is None or item.get("kind") != "toggle_icon":
            return False

        widget = self.toggle_icon_widgets.get(item["id"])
        if widget is None:
            return False

        state = self._state_value(item)
        if state is None:
            return None

        width = int(item.get("width", 24))
        height = int(item.get("height", 24))
        path = self._toggle_icon_path(item, state)
        widget.setFixedSize(width, height)
        widget.setProperty("stateOn", bool(state))

        icon = QtGui.QIcon(path) if path else QtGui.QIcon()
        pixmap = icon.pixmap(width, height) if path else QtGui.QPixmap()
        if not pixmap.isNull():
            widget.setPixmap(pixmap)
            widget.setText("")
        else:
            widget.setPixmap(QtGui.QPixmap())
            widget.setText("?")
        return bool(state)

    def refresh_state_buttons(self):
        for item_id in list(self.state_button_widgets.keys()):
            try:
                self.refresh_state_button(item_id)
            except Exception:
                pass
        for item_id in list(self.toggle_icon_widgets.keys()):
            try:
                self.refresh_toggle_icon(item_id)
            except Exception:
                pass

    def run_state_binding(self, item_or_id, binding=None, event=None):
        item = (
            item_or_id
            if isinstance(item_or_id, dict)
            else self.find_item(item_or_id)
        )
        if item is None or item.get("kind") not in (
            "toggle_button",
            "toggle_icon",
        ):
            return None

        state = self._state_value(item)
        if state is None:
            return None

        if state:
            code = item.get("state_off_script", "")
            language = item.get("state_off_language", "python")
        else:
            code = item.get("state_on_script", "")
            language = item.get("state_on_language", "python")

        result = execute_script_result(
            code,
            language=language,
            toolbox=self,
            parent=self,
            extra_namespace={
                "toolbox": self,
                "item": item,
                "event": event or {},
            },
            context="state:{0}".format(
                item.get("name", item.get("id", "toggle"))
            ),
            notify=True
        )

        if item.get("state_source", "internal") == "internal":
            if result.success:
                self.store_value(item.get("id"), not bool(state))
        else:
            self.refresh_state_buttons()
        return result

    # ------------------------------------------------------------------
    # Runtime
    # ------------------------------------------------------------------

    def rebuild(self):
        self.field_widgets = {}
        self.state_button_widgets = {}
        self.toggle_icon_widgets = {}

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

    def run_item(self, item_id):
        item = self.find_item(item_id)
        if item is None or item.get("kind") not in (
            "button",
            "toggle_button",
            "toggle_icon",
        ):
            return None

        normalized_id = text_type(item.get("id", item_id))
        if normalized_id in self._binding_widget_click_suppression:
            self._binding_widget_click_suppression.discard(normalized_id)
            return None

        return self.dispatch_binding_event(
            item,
            "click",
            mouse_button="left",
            modifiers=[]
        )

    # ------------------------------------------------------------------
    # Updater
    # ------------------------------------------------------------------

    def manual_check_for_updates(self):
        self.check_for_updates(manual=True)

    def check_for_updates(self, manual=False):
        if (
            self.update_check_thread is not None and
            self.update_check_thread.isRunning()
        ):
            return

        self._manual_update_check = bool(manual)
        if manual:
            self.statusBar().showMessage(
                "Checking for Script Toolbox updates..."
            )

        self.update_check_thread = UpdateCheckThread(self)
        self.update_check_thread.completed.connect(
            self.update_check_finished
        )
        self.update_check_thread.start()

    def update_check_finished(self, result):
        self.update_info = result
        error = result.get("error")

        if error:
            self.update_button.setVisible(False)
            self.statusBar().showMessage(
                "Update check failed: {0}".format(error),
                12000
            )
            self._manual_update_check = False
            return

        if not result.get("available", False):
            self.update_button.setVisible(False)
            if self._manual_update_check:
                self.statusBar().showMessage(
                    "Script Toolbox {0} is up to date.".format(
                        PLUGIN_VERSION
                    ),
                    5000
                )
            self._manual_update_check = False
            return

        latest = result.get("latest_version") or ""
        self.update_button.setText("UPDATE {0}".format(latest))
        self.update_button.setToolTip(
            "Script Toolbox {0} is available. Current version: {1}".format(
                latest,
                PLUGIN_VERSION
            )
        )
        self.update_button.setVisible(True)
        self.statusBar().showMessage(
            "Script Toolbox {0} is available.".format(latest),
            7000
        )
        self._manual_update_check = False

    def install_available_update(self):
        if not self.update_info:
            return

        release = self.update_info.get("release")
        if not release:
            return

        latest = self.update_info.get("latest_version", "")
        answer = QtGui.QMessageBox.question(
            self,
            "Update Script Toolbox",
            (
                "Install Script Toolbox {0}?\n\n"
                "Your toolbox configuration is stored separately and "
                "will not be replaced. Script Toolbox will reload "
                "automatically after the update."
            ).format(latest),
            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
            QtGui.QMessageBox.Yes
        )
        if answer != QtGui.QMessageBox.Yes:
            return

        self.update_button.setEnabled(False)
        self.update_button.setText("UPDATING...")
        self.statusBar().showMessage(
            "Installing Script Toolbox {0}...".format(latest)
        )

        self.update_install_thread = UpdateInstallThread(release, self)
        self.update_install_thread.completed.connect(
            self.update_install_finished
        )
        self.update_install_thread.start()

    def update_install_finished(self, result):
        if not result.get("installed", False):
            self.update_button.setEnabled(True)
            latest = (
                self.update_info.get("latest_version", "")
                if self.update_info
                else ""
            )
            self.update_button.setText(
                "UPDATE {0}".format(latest).strip()
            )
            QtGui.QMessageBox.critical(
                self,
                "Update Failed",
                result.get("error", "Unknown update error.")
            )
            return

        version = result.get("version", "")
        self.update_button.setText("RELOADING...")
        self.update_button.setEnabled(False)
        self.statusBar().showMessage(
            "Script Toolbox {0} installed. Reloading...".format(version)
        )

        try:
            if self.update_install_thread is not None:
                self.update_install_thread.wait(2000)
        except Exception:
            pass

        QtCore.QTimer.singleShot(150, self.hot_reload_after_update)

    def hot_reload_after_update(self):
        try:
            from ..bootstrap import hot_reload_toolbox
            hot_reload_toolbox()
        except Exception as exc:
            self.update_button.setText(
                "RESTART {0}".format(HOST.display_name.upper())
            )
            self.update_button.setEnabled(False)
            QtGui.QMessageBox.warning(
                self,
                "Update Installed",
                (
                    "The update was installed, but Script Toolbox "
                    "could not reload itself.\n\n"
                    "Restart {0} to load the new version.\n\n"
                    "{1}"
                ).format(HOST.display_name, text_type(exc))
            )

    # ------------------------------------------------------------------
    # Editor / reload
    # ------------------------------------------------------------------

    def open_interface_editor(self):
        from .interface_editor import InterfaceEditor

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

        self.editor_window = InterfaceEditor(self, parent=self)
        self.editor_window.show()
        self.editor_window.raise_()
        self.editor_window.activateWindow()

    def reload_config(self):
        self.config = load_config()
        self.rebuild()
        self.statusBar().showMessage("Config reloaded.", 2500)


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
    _TOOLBOX = ScriptToolbox(parent=main_window())
    _TOOLBOX.show()
    _TOOLBOX.raise_()
    _TOOLBOX.activateWindow()
    return _TOOLBOX


__all__ = [
    "ScriptToolbox",
    "close_toolbox",
    "show",
]
