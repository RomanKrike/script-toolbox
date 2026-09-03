# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore
from ..compat import QtGui
from ..compat import cmds
from ..compat import maya_main_window
from ..compat import shift_pressed
from ..constants import PLUGIN_VERSION
from ..constants import WINDOW_OBJECT_NAME
from ..core.config import load_config
from ..core.config import save_config
from ..core.executor import execute_script
from ..core.values import find_item
from ..core.values import get_value as get_document_value
from ..core.values import store_value as store_document_value
from ..model import walk_items
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
            parent or maya_main_window()
        )

        self.setObjectName(
            WINDOW_OBJECT_NAME
        )
        self.setWindowTitle(
            "Script Toolbox {0}".format(
                PLUGIN_VERSION
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
        self._selection_signature = None

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

        # Check once per Maya session/window without blocking the UI thread.
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
            "SCRIPT TOOLBOX  v{0}".format(
                PLUGIN_VERSION
            )
        )
        title.setObjectName(
            "ToolboxTitle"
        )
        title.setToolTip(
            "Script Toolbox {0}".format(
                PLUGIN_VERSION
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
            "Click = script | Shift+Click = alternate script | Name = script ID"
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
        item = store_document_value(
            self.config,
            key,
            value
        )

        if item is None:
            return False

        self.save()
        return True

    def set_value(
        self,
        key,
        value
    ):
        item = self.find_item(
            key
        )

        if not self.store_value(
            key,
            value
        ):
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
        return self.set_value(
            key,
            value
        )

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

    def field_display_text(
        self,
        key
    ):
        item = self.find_item(
            key
        )

        if (
            item is None or
            item.get("kind") != "field"
        ):
            return ""

        value = item.get(
            "value",
            ""
        )

        if value is None:
            return ""

        if isinstance(
            value,
            (list, tuple)
        ):
            return ", ".join(
                text_type(entry)
                for entry in value
            )

        return text_type(
            value
        )

    def refresh_field_widget(
        self,
        key
    ):
        item = self.find_item(
            key
        )

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

    def field_scene_objects(
        self,
        key
    ):
        item = self.find_item(
            key
        )

        if (
            item is None or
            item.get("kind") != "field"
        ):
            return []

        value = item.get(
            "value",
            ""
        )

        if isinstance(
            value,
            (list, tuple)
        ):
            candidates = [
                text_type(entry)
                for entry in value
            ]
        else:
            value = text_type(
                value or ""
            )

            if value and cmds.objExists(
                value
            ):
                candidates = [
                    value
                ]
            else:
                normalized = (
                    value
                    .replace(";", "\n")
                    .replace(",", "\n")
                )

                candidates = [
                    part.strip()
                    for part in normalized.splitlines()
                    if part.strip()
                ]

        return [
            candidate
            for candidate in candidates
            if cmds.objExists(
                candidate
            )
        ]

    def select_field_objects(
        self,
        key
    ):
        objects = self.field_scene_objects(
            key
        )

        if not objects:
            return False

        try:
            cmds.select(
                objects,
                replace=True
            )
            return True
        except Exception:
            return False

    def refresh_selection_fields(
        self,
        force=False
    ):
        selection_fields = [
            item
            for item in self.all_items()
            if (
                item.get("kind") == "field" and
                item.get("source") == "selection"
            )
        ]

        if not selection_fields:
            return

        try:
            raw_selection = cmds.ls(
                selection=True,
                long=True
            ) or []
        except Exception:
            raw_selection = []

        signature = tuple(
            raw_selection
        )

        if (
            not force and
            signature == self._selection_signature
        ):
            return

        self._selection_signature = signature

        for item in selection_fields:
            try:
                if item.get(
                    "long_names",
                    False
                ):
                    values = list(
                        raw_selection
                    )
                else:
                    values = cmds.ls(
                        raw_selection,
                        long=False
                    ) or []

                if not item.get(
                    "multiple",
                    True
                ):
                    values = values[:1]

                item["value"] = values
                self.refresh_field_widget(
                    item["id"]
                )
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Runtime
    # ------------------------------------------------------------------

    def rebuild(self):
        self.field_widgets = {}

        while self.content_layout.count() > 1:
            layout_item = self.content_layout.takeAt(
                0
            )
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

        self.refresh_selection_fields(
            force=True
        )

    def run_item(
        self,
        item_id
    ):
        item = self.find_item(
            item_id
        )

        if (
            not item or
            item.get("kind") != "button"
        ):
            return

        code = item.get(
            "click_script",
            ""
        )

        if (
            shift_pressed() and
            item.get(
                "shift_script",
                ""
            ).strip()
        ):
            code = item.get(
                "shift_script",
                ""
            )

        success = execute_script(
            code,
            item.get(
                "language",
                "python"
            ),
            parent=self,
            toolbox=self
        )

        if success:
            self.statusBar().showMessage(
                "Executed: {0}".format(
                    item.get(
                        "label",
                        item["name"]
                    )
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
                "RESTART MAYA"
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
                    "Restart Maya to load the new version.\n\n"
                    "{0}"
                ).format(
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
        parent=maya_main_window()
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
