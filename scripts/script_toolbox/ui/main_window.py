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
from ..core.values import normalize_value as normalize_document_value
from ..core.values import store_value as store_document_value
from ..model import walk_items
from ..model.item_builtins import register_builtin_items
from ..model.item_registry import ITEM_TYPES
from ..model.items import safe_color
from ..pycompat import text_type
from ..style import STYLE
from ..style import apply_window_icon
from ..style import metrics
from ..style import toolbar_icon
from ..style.palette import CONTENT_BG
from .layout_helpers import configure_layout
from .update_ui import UpdateCheckThread
from .update_ui import UpdateInstallThread
from .state_toggle_hooks import StateToggleBehaviorMixin
from .runtime_value_sync import RuntimeValueMixin
from .expression_runtime import ExpressionRuntimeMixin


_TOOLBOX = None


def _definition(item):
    register_builtin_items()
    if not isinstance(item, dict):
        return None
    return ITEM_TYPES.get(item.get("kind"))


def _props(item):
    value = item.get("props", {}) if isinstance(item, dict) else {}
    return value if isinstance(value, dict) else {}


def _ui(item):
    value = item.get("ui", {}) if isinstance(item, dict) else {}
    return value if isinstance(value, dict) else {}


def _has_capability(item, capability):
    definition = _definition(item)
    return bool(definition and definition.has_capability(capability))


class ToolboxStatusBar(QtGui.QStatusBar):
    """Shared footer with a persistent Logs label and transient app status."""

    def __init__(self, parent=None):
        QtGui.QStatusBar.__init__(self, parent)
        self.setObjectName("ToolboxStatusBar")

        try:
            self.setSizeGripEnabled(False)
        except Exception:
            pass

        self._message = ""
        self._status_callback = None
        self._persistent_message = ""
        self._persistent_callback = None
        self._persistent_tooltip = ""

        self.logs_icon = QtGui.QLabel(self)
        self.logs_icon.setObjectName("StatusLogsIcon")
        self.logs_icon.setAlignment(QtCore.Qt.AlignCenter)
        self.logs_icon.setFixedWidth(28)
        self.logs_icon.setToolTip("Logs")

        icon = toolbar_icon("console")
        if not icon.isNull():
            self.logs_icon.setPixmap(
                icon.pixmap(
                    QtCore.QSize(
                        16,
                        16
                    )
                )
            )

        self.addWidget(self.logs_icon)

        self.status_action = QtGui.QToolButton(self)
        self.status_action.setObjectName("StatusAction")
        self.status_action.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)
        self.status_action.setAutoRaise(True)
        self.status_action.setVisible(False)
        self.status_action.clicked.connect(self._trigger_status_action)
        self.addPermanentWidget(self.status_action)

        self._clear_timer = QtCore.QTimer(self)
        self._clear_timer.setSingleShot(True)
        self._clear_timer.timeout.connect(self.clearMessage)

    def _trigger_status_action(self, checked=False):
        callback = self._status_callback
        if callback is not None:
            callback()

    def _display_status(self, message, callback=None, tooltip=""):
        self._message = text_type(message or "")
        self._status_callback = callback
        self.status_action.setText(self._message)
        self.status_action.setToolTip(text_type(tooltip or ""))
        self.status_action.setVisible(bool(self._message))

    def _restore_persistent_status(self):
        self._display_status(
            self._persistent_message,
            callback=self._persistent_callback,
            tooltip=self._persistent_tooltip
        )

    def show_status(self, message, timeout=0, callback=None, tooltip=""):
        self._clear_timer.stop()
        self._display_status(
            message,
            callback=callback,
            tooltip=tooltip
        )
        if self._message and timeout:
            self._clear_timer.start(int(timeout))

    def show_action(self, message, callback, tooltip=""):
        self._persistent_message = text_type(message or "")
        self._persistent_callback = callback
        self._persistent_tooltip = text_type(tooltip or "")
        self.show_status(
            self._persistent_message,
            callback=self._persistent_callback,
            tooltip=self._persistent_tooltip
        )

    def clear_action(self):
        self._persistent_message = ""
        self._persistent_callback = None
        self._persistent_tooltip = ""
        self._clear_timer.stop()
        self._display_status("")

    def showMessage(self, message, timeout=0):
        self.show_status(message, timeout=timeout)

    def clearMessage(self):
        self._clear_timer.stop()
        self._restore_persistent_status()

    def currentMessage(self):
        return self._message


class ScriptToolbox(StateToggleBehaviorMixin, RuntimeValueMixin, ExpressionRuntimeMixin, QtGui.QMainWindow):

    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent or main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)
        self.setWindowTitle(
            "Script Toolbox {0} - {1}".format(
                PLUGIN_VERSION,
                HOST.display_name
            )
        )
        apply_window_icon(
            self
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

        from .managed_presets import SourceScheduler
        self.preset_source_scheduler = SourceScheduler(self)

        self.selection_timer = QtCore.QTimer(self)
        self.selection_timer.setInterval(300)
        self.selection_timer.timeout.connect(self.refresh_selection_fields)
        self.selection_timer.start()

        self.update_check_timer = QtCore.QTimer(self)
        self.update_check_timer.setSingleShot(True)
        self.update_check_timer.timeout.connect(self.check_for_updates)
        self.update_check_timer.start(1200)

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

        self._build_menu_bar(root)

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
        self.setStatusBar(ToolboxStatusBar(self))

    def _styled_menu(self, title):
        menu = self.menu_bar.addMenu(title)
        menu.setStyleSheet(STYLE)
        return menu

    def _build_menu_bar(self, root):
        self.menu_bar = QtGui.QMenuBar(self.centralWidget())
        self.menu_bar.setObjectName("ToolboxMenuBar")

        set_native = getattr(self.menu_bar, "setNativeMenuBar", None)
        if set_native is not None:
            set_native(False)

        self.editor_menu = self._styled_menu("Editor")
        self.open_editor_action = self.editor_menu.addAction("Open Editor")
        self.open_editor_action.triggered.connect(
            self._open_editor_from_menu
        )

        self.settings_menu = self._styled_menu("Settings")
        self.settings_action = self.settings_menu.addAction("Open Settings")
        settings_handler = getattr(self, "open_settings_dialog", None)
        self.settings_action.setEnabled(settings_handler is not None)
        self.settings_action.triggered.connect(
            self._open_settings_from_menu
        )

        self.settings_menu.addSeparator()
        self.reload_action = self.settings_menu.addAction("Reload Config")
        self.reload_action.triggered.connect(
            self._reload_config_from_menu
        )

        self.check_updates_action = self.settings_menu.addAction(
            "Check for Updates"
        )
        self.check_updates_action.triggered.connect(
            self._check_updates_from_menu
        )

        self.help_menu = self._styled_menu("Help")

        root.addWidget(self.menu_bar)

    def _open_editor_from_menu(self, checked=False):
        return self.open_interface_editor()

    def _open_settings_from_menu(self, checked=False):
        callback = getattr(
            self,
            "open_settings_dialog",
            None
        )
        if callback is not None:
            return callback()
        return None

    def _reload_config_from_menu(self, checked=False):
        return self.reload_config()

    def _check_updates_from_menu(self, checked=False):
        return self.manual_check_for_updates()

    # ------------------------------------------------------------------
    # Config / value API
    # ------------------------------------------------------------------

    def save(self):
        save_config(self.config)

    def all_items(self):
        return walk_items(self.config)

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
                ui = _ui(item)
                self.statusBar().showMessage(
                    "Executed: {0}".format(
                        ui.get("label", item.get("name", "Item"))
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
        self.sync_runtime_value(key)
        self.refresh_expressions(key)
        return True

    def set_value(self, key, value):
        item = self.find_item(key)
        if not self.store_value(key, value):
            return False

        if item is not None and _has_capability(item, "field_widget"):
            self.refresh_field_widget(item["id"])
            return True

        if item is not None and item["id"] not in self.value_widgets:
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
        if item is None or not _has_capability(item, "field_widget"):
            return []

        props = _props(item)
        value = props.get("value", "")
        if value is None:
            return []

        if isinstance(value, (list, tuple)):
            return [
                text_type(entry)
                for entry in value
                if text_type(entry).strip()
            ]

        value = text_type(value or "")
        if props.get("multiple", True):
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
        if item is None or not _has_capability(item, "field_widget"):
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
        if item is None or not _has_capability(item, "field_widget"):
            return False
        props = _props(item)

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

        if not props.get("multiple", True):
            result = result[-1:]
            value = result[0] if result else ""
        else:
            value = result
        return self.set_value(key, value)

    def remove_from_field(self, key, values=None):
        item = self.find_item(key)
        if item is None or not _has_capability(item, "field_widget"):
            return False
        props = _props(item)

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
        if not props.get("multiple", True):
            value = result[0] if result else ""
        else:
            value = result
        return self.set_value(key, value)

    def clear_field(self, key):
        item = self.find_item(key)
        if item is None or not _has_capability(item, "field_widget"):
            return False
        props = _props(item)
        return self.set_value(
            key,
            [] if props.get("multiple", True) else ""
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

        selection_fields = []
        for item in self.all_items():
            if not _has_capability(item, "field_widget"):
                continue
            props = _props(item)
            if props.get("source") == "selection":
                selection_fields.append(item)

        for item in selection_fields:
            try:
                props = item.setdefault("props", {})
                values = HOST.current_selection(
                    long_names=bool(props.get("long_names", False))
                ) or []
                if not props.get("multiple", True):
                    values = values[:1]
                    new_value = values[0] if values else ""
                else:
                    new_value = values

                old_value = props.get("value", "")
                new_value = normalize_document_value(item, new_value)
                props["value"] = new_value
                self.refresh_field_widget(item["id"])
                if old_value != new_value:
                    self._run_on_change(item, old_value, new_value)
                    self.refresh_expressions(item["id"])
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
        props = _props(item)
        if props.get("state_source", "internal") == "script":
            return evaluate_python_state(
                props.get("state_get_script", ""),
                toolbox=self,
                parent=self
            )
        return bool(props.get("value", False))

    def refresh_state_button(self, key):
        item = self.find_item(key)
        definition = _definition(item)
        if (
            item is None or
            definition is None or
            not definition.has_capability("state_toggle") or
            not definition.has_capability("native_button")
        ):
            return False

        widget = self.state_button_widgets.get(item["id"])
        if widget is None:
            return False

        state = self._state_value(item)
        if state is None:
            return None

        props = _props(item)
        ui = _ui(item)
        label = props.get(
            "state_on_label" if state else "state_off_label",
            ui.get("label", item.get("name", "Toggle"))
        )
        color = safe_color(
            props.get("state_on_color" if state else "state_off_color")
        )
        rgb = [int(value * 255) for value in color]

        widget.setText("" if props.get("icon_only", False) else text_type(label))
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
        props = _props(item)
        return os.path.expanduser(
            os.path.expandvars(
                text_type(
                    props.get(
                        "state_on_path" if state else "state_off_path",
                        ""
                    ) or ""
                )
            )
        )

    def refresh_toggle_icon(self, key):
        item = self.find_item(key)
        definition = _definition(item)
        if (
            item is None or
            definition is None or
            not definition.has_capability("state_toggle") or
            "state_on_path" not in definition.fields
        ):
            return False

        widget = self.toggle_icon_widgets.get(item["id"])
        if widget is None:
            return False

        state = self._state_value(item)
        if state is None:
            return None

        props = _props(item)
        width = int(props.get("width", 24))
        height = int(props.get("height", 24))
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
        definition = _definition(item)
        if (
            item is None or
            definition is None or
            not definition.has_capability("state_toggle")
        ):
            return None

        state = self._state_value(item)
        if state is None:
            return None

        props = _props(item)
        if state:
            code = props.get("state_off_script", "")
            language = props.get("state_off_language", "python")
        else:
            code = props.get("state_on_script", "")
            language = props.get("state_on_language", "python")

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

        if props.get("state_source", "internal") == "internal":
            if result.success:
                self.store_value(item.get("id"), not bool(state))
        else:
            self.refresh_state_buttons()
        return result

    # ------------------------------------------------------------------
    # Runtime
    # ------------------------------------------------------------------

    def rebuild(self):
        from ..core.values import invalidate_document_index
        from ..core.preset_references import PresetResolver
        from ..core.preset_sources import SourceRegistry
        if not hasattr(self, "preset_resolver"):
            registry = SourceRegistry()
            sources = dict((source['id'], source) for source in registry.sources())
            self.preset_resolver = PresetResolver(registry, packages={}, sources=sources)
            self.preset_resolver.loading = bool(sources)
            self._preset_snapshot_closed = False
            self._preset_snapshot_loading = False
            from .preset_snapshot_jobs import SnapshotLoader
            self.preset_snapshot_loader = SnapshotLoader(self, registry)
            if sources:
                self.request_preset_snapshot()
        self.preset_resolver.resolve_document(self.config)
        invalidate_document_index(self.config)
        from .runtime_surface import RuntimeSurface, capture_view_state
        state = capture_view_state(self)
        surface = RuntimeSurface(self, self.config).prepare(self.config)
        try:
            surface.activate(self, state)
        except Exception:
            surface.dispose()
            raise
        self.refresh_selection_fields(force=True)
        self.refresh_state_buttons()

    def run_item(self, item_id):
        item = self.find_item(item_id)
        definition = _definition(item)
        if (
            item is None or
            definition is None or
            not definition.has_capability("native_button") or
            "click" not in definition.events
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
            self.statusBar().showMessage("Checking for updates...")

        self.update_check_thread = UpdateCheckThread(self)
        self.update_check_thread.completed.connect(
            self.update_check_finished
        )
        self.update_check_thread.start()

    @QtCore.Slot(object)
    def update_check_finished(self, result):
        self.update_info = result
        error = result.get("error")

        if error:
            self.statusBar().show_status(
                "Update check failed",
                timeout=12000,
                tooltip=text_type(error)
            )
            self._manual_update_check = False
            return

        if not result.get("available", False):
            self.statusBar().clear_action()
            if self._manual_update_check:
                self.statusBar().showMessage("You're up to date", 5000)
            self._manual_update_check = False
            return

        latest = result.get("latest_version") or ""
        label = (
            "Update {0} available >".format(latest)
            if latest
            else "Update available >"
        )
        tooltip = (
            "Script Toolbox {0} is available. Current version: {1}".format(
                latest,
                PLUGIN_VERSION
            )
            if latest
            else "A Script Toolbox update is available."
        )
        self.statusBar().show_action(
            label,
            self.install_available_update,
            tooltip=tooltip
        )
        self._manual_update_check = False

    def install_available_update(self):
        if self.update_install_thread is not None and self.update_install_thread.isRunning():
            self.statusBar().showMessage("An update is already running.")
            return
        if not self.update_info:
            return

        release = self.update_info.get("release")
        if not release:
            return

        latest = self.update_info.get("latest_version", "")
        lifecycle = (
            "restart"
            if HOST.key == "standalone"
            else "reload"
        )
        answer = QtGui.QMessageBox.question(
            self,
            "Update Script Toolbox",
            (
                "Install Script Toolbox {0}?\n\n"
                "Your toolbox configuration is stored separately and "
                "will not be replaced. Script Toolbox will {1} "
                "automatically after the update."
            ).format(
                latest,
                lifecycle
            ),
            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
            QtGui.QMessageBox.Yes
        )
        if answer != QtGui.QMessageBox.Yes:
            return
        # The confirmation dialog runs a nested Qt event loop. Another action
        # may have started an install while this dialog was open.
        if self.update_install_thread is not None and self.update_install_thread.isRunning():
            return

        self.statusBar().showMessage(
            "Installing Script Toolbox {0}...".format(latest)
        )

        self.update_install_thread = UpdateInstallThread(release, self)
        self.update_install_thread.completed.connect(
            self.update_install_finished
        )
        self.update_install_thread.start()

    @QtCore.Slot(object)
    def update_install_finished(self, result):
        if not (result.get("installed", False) or result.get("staged", False)):
            error = result.get("error", "Unknown update error.")
            self.statusBar().show_status(
                "Update failed",
                timeout=12000,
                tooltip=text_type(error)
            )
            QtGui.QMessageBox.critical(
                self,
                "Update Failed",
                error
            )
            return

        version = result.get("version", "")

        try:
            if self.update_install_thread is not None:
                self.update_install_thread.wait(2000)
        except Exception:
            pass

        if result.get("restart_required", False):
            self.statusBar().showMessage(
                "Script Toolbox {0} staged. Restarting...".format(
                    version
                )
            )

            if result.get(
                "external_restart_scheduled",
                False
            ):
                QtCore.QTimer.singleShot(
                    150,
                    self.exit_for_standalone_update
                )
                return

            QtGui.QMessageBox.warning(
                self,
                "Update Installed",
                (
                    "Script Toolbox {0} was installed, but an automatic "
                    "restart could not be scheduled. Restart Standalone "
                    "manually to finish the update."
                ).format(version)
            )
            return

        self.statusBar().showMessage(
            "Script Toolbox {0} installed. Reloading...".format(version)
        )
        QtCore.QTimer.singleShot(150, self.hot_reload_after_update)

    def exit_for_standalone_update(self):
        application = QtGui.QApplication.instance()

        if application is not None:
            application.quit()
            return

        self.close()

    def hot_reload_after_update(self):
        try:
            from ..bootstrap import hot_reload_toolbox
            hot_reload_toolbox()
        except Exception as exc:
            self.statusBar().show_status(
                "Restart required",
                tooltip=(
                    "Restart {0} to load the installed update. {1}"
                ).format(HOST.display_name, text_type(exc))
            )
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

    def request_preset_snapshot(self):
        if getattr(self, '_preset_snapshot_closed', False):
            return
        self._preset_snapshot_loading = True
        self.statusBar().showMessage("Loading local preset libraries...")
        self.preset_snapshot_loader.request(self._preset_snapshot_ready, self.preset_resolver)

    def _preset_snapshot_ready(self, result):
        self._preset_snapshot_loading = False
        if not result['ok']:
            self.preset_resolver.loading = False
            self.statusBar().showMessage("Preset libraries could not be loaded: " + result['error'])
            return
        from ..core.preset_references import authored_document
        from .runtime_surface import RuntimeSurface, capture_view_state
        resolver = result['value']
        candidate = authored_document(self.config)
        resolver.resolve_document(candidate)
        state = capture_view_state(self)
        try:
            surface = RuntimeSurface(self, candidate, resolver).prepare(candidate)
        except Exception as exc:
            self.statusBar().showMessage("Preset interface could not be prepared: " + text_type(exc))
            return
        old_document, old_resolver = self.config, self.preset_resolver
        self.config, self.preset_resolver = candidate, resolver
        try:
            surface.activate(self, state)
        except Exception as exc:
            self.config, self.preset_resolver = old_document, old_resolver
            surface.dispose()
            self.statusBar().showMessage("Preset interface could not be activated: " + text_type(exc))
            return
        if getattr(self, 'config_store', None) is not None:
            self.config_store.replace_document(candidate, dirty=self.config_store.dirty)
        self.refresh_selection_fields(force=True)
        self.refresh_state_buttons()
        self.statusBar().showMessage("Preset libraries loaded.", 2500)

    def open_interface_editor(self):
        from .bootstrap import initialize_ui
        InterfaceEditor = initialize_ui().InterfaceEditor

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
        self.request_preset_snapshot()
        self.statusBar().showMessage("Config reloaded. Loading preset libraries...", 2500)


def close_toolbox():
    from .debounced_main_window import close_toolbox as close_final_window
    return close_final_window()


def show():
    from .debounced_main_window import show as show_final_window
    return show_final_window()


__all__ = [
    "ScriptToolbox",
    "close_toolbox",
    "show",
]
