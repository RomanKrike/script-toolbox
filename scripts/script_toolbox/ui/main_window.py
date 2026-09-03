# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore
from ..compat import QtGui
from ..compat import cmds
from ..compat import maya_main_window
from ..compat import shift_pressed
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
            "Script Toolbox"
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
            "SCRIPT TOOLBOX"
        )
        title.setObjectName(
            "ToolboxTitle"
        )

        top_layout.addWidget(
            title
        )
        top_layout.addStretch(
            1
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
