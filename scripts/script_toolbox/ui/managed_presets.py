# -*- coding: utf-8 -*-
"""Qt presentation of managed parameters; network work never runs on Qt."""
from __future__ import print_function

import threading
import os
import uuid
import time
try:
    import queue
except ImportError:
    import Queue as queue

from ..compat import HOST, QtCore, QtGui
from ..core.preset_references import iter_targets, linked_preset
from ..core.presets import default_library_path
from ..core.preset_sources import SourceRegistry, POLICIES
from ..core.preset_sync import SyncService, MANIFEST, read_json, validate_manifest
from ..pycompat import text_type
from ..qt_compat import qt_exec
from ..style.metrics import SETTINGS_PAGE_MARGINS, SETTINGS_PAGE_SPACING
from ..style import metrics
from .settings_components import (build_page_header, build_section_form, build_simple_section,
                                  configure_settings_scroll_area, mark_secondary_text, mark_status_text)

ROLE_TARGET = QtCore.Qt.UserRole + 51
ROLE_LIBRARY_PRESET = QtCore.Qt.UserRole + 52


class ReferenceInfoLabel(QtGui.QLabel):
    """Read-only inspector with the existing write/cleanup contract."""
    def write_to_item(self):
        pass


def render_broken_reference(owner, item, compact=False):
    label = QtGui.QLabel("{0} (broken reference)".format(item["ui"]["label"]))
    label.setToolTip(item["ui"].get("tooltip") or "Target is not available in the local cache.")
    label.setEnabled(False)
    return label


def populate_managed_presets(editor, tree):
    resolver = editor.preset_resolver
    for source_id, source in sorted(resolver.sources.items()):
        if not source["enabled"]:
            continue
        group = QtGui.QTreeWidgetItem([source["name"]])
        group.setFlags(group.flags() & ~QtCore.Qt.ItemIsSelectable)
        categories = {}
        package = resolver.packages.get(source_id)
        if package is not None:
            for preset in package["presets"]:
                if preset.get("dcc", "all") not in ("all", getattr(HOST, "key", "")):
                    continue
                category = text_type(preset.get("category") or "General")
                parent = group
                path = []
                for part in category.split("/"):
                    path.append(part)
                    key = "/".join(path)
                    if key not in categories:
                        category_item = QtGui.QTreeWidgetItem([part])
                        category_item.setFlags(category_item.flags() & ~QtCore.Qt.ItemIsSelectable)
                        parent.addChild(category_item)
                        categories[key] = category_item
                    parent = categories[key]
                item = QtGui.QTreeWidgetItem([preset.get("label", preset["id"])])
                item.setData(0, ROLE_LIBRARY_PRESET, source_id + "/" + preset["id"])
                item.setToolTip(0, preset.get("description", "Add the complete linked preset."))
                targets = list(iter_targets(preset["root"]))
                if len(targets) == 1 and targets[0] is preset["root"]:
                    item.setData(0, ROLE_TARGET, source_id + "/" + preset["id"] + "/" + targets[0]["id"])
                else:
                    for target in targets:
                        child = QtGui.QTreeWidgetItem([target["ui"]["label"]])
                        child.setData(0, ROLE_TARGET, source_id + "/" + preset["id"] + "/" + target["id"])
                        child.setToolTip(0, "Read-only definition: " + target["name"])
                        item.addChild(child)
                categories[category].addChild(item)
                categories[category].setExpanded(True)
        else:
            group.setToolTip(0, "Not installed. Synchronize this library in Settings.")
        tree.addTopLevelItem(group)
        group.setExpanded(True)
        for category_item in categories.values():
            category_item.setExpanded(True)


def library_address(item):
    if item is None:
        return None
    value = item.data(0, ROLE_LIBRARY_PRESET)
    try:
        value = value.toString()
    except AttributeError:
        pass
    value = text_type(value or "")
    return value.split("/", 1) if value else None


def insert_library_preset(editor, palette_item, column=0):
    address = library_address(palette_item)
    if address is None:
        return None
    source_id, preset_id = address
    package = editor.preset_resolver.packages[source_id]
    preset = next(p for p in package["presets"] if p["id"] == preset_id)
    editor.sync_working_from_tree()
    clone = editor.document_controller.clone_subtree(preset["root"], editor._used_names())
    clone = linked_preset(preset["root"], clone, source_id, preset_id, editor.preset_resolver)
    tree_item = editor._insert_cloned_tree_item(clone, sibling=False)
    editor.tree.setCurrentItem(tree_item)
    tree_item.setExpanded(True)
    editor.fix_tree_structure()
    editor.tree_changed()
    return tree_item


def target_address(item):
    if item is None:
        return None
    value = item.data(0, ROLE_TARGET)
    try:
        value = value.toString()
    except AttributeError:
        pass
    value = text_type(value or "")
    return value.split("/", 2) if value else None


def insert_reference(editor, palette_item, column=0):
    address = target_address(palette_item)
    if address is None:
        return None
    resolver = editor.preset_resolver
    editor.sync_working_from_tree()
    reference = resolver.create_reference(*address)
    reference["name"] = editor._unique_name(reference["name"], editor._used_names())
    tree_item = editor._insert_cloned_tree_item(reference, sibling=False)
    editor.tree.setCurrentItem(tree_item)
    editor.fix_tree_structure()
    editor.tree_changed()
    return tree_item


def reference_tooltip(reference, resolver):
    props = reference["props"]
    source = resolver.sources.get(props["source"], {})
    message = "Referenced from: {0} / {1} / {2}\nDefinition is read only.".format(
        source.get("name", props["source"]), props["preset"], props["parameter"])
    try:
        target = resolver.resolve(reference)
        return message + "\n" + target["kind"], False
    except (ValueError, TypeError, KeyError) as exc:
        return message + "\n" + text_type(exc), True


class BackgroundJob(object):
    """Daemon filesystem worker, with results polled by a UI-owned timer.

    No QObject is owned by the worker, so closing a dialog/window does not
    destroy a running QThread or leave callbacks into deleted Qt widgets.
    """
    def __init__(self, action):
        self.results = queue.Queue()
        def run():
            try:
                result = {"ok": True, "value": action()}
            except Exception as exc:
                result = {"ok": False, "error": text_type(exc)}
            self.results.put(result)
        self.thread = threading.Thread(target=run)
        self.thread.daemon = True
        self.thread.start()

    def poll(self):
        try:
            return self.results.get_nowait()
        except queue.Empty:
            return None


class SourceScheduler(QtCore.QObject):
    def __init__(self, parent):
        QtCore.QObject.__init__(self, parent)
        self.registry = SourceRegistry()
        self.service = SyncService(self.registry)
        self.job = None
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(60000)
        self.timer.timeout.connect(self.tick)
        self.timer.start()
        QtCore.QTimer.singleShot(0, self.startup)

    def startup(self):
        self.tick(startup=True)

    def tick(self, startup=False):
        if self.job is not None:
            if self.job.poll() is None:
                return
            self.job = None
        # Even local cache validation can be slow; keep it in the worker.
        service, registry = self.service, self.registry
        def update():
            for source in registry.sources():
                if service.due(source, startup=startup):
                    try:
                        service.check(source["id"], download=True)
                    except Exception:
                        # A concurrent DCC/manual sync owns the lock; retry later.
                        continue
        self.job = BackgroundJob(update)


class SavePresetDialog(QtGui.QDialog):
    """Collect all publishing options in one validated form."""
    def __init__(self, sources, label, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.sources = sources
        self.setWindowTitle("Save Selected as Preset")
        layout = QtGui.QVBoxLayout(self)
        layout.setSpacing(SETTINGS_PAGE_SPACING)
        section, section_layout = build_simple_section("Preset", parent=self)
        form = build_section_form()
        self.library = QtGui.QComboBox()
        self.library.addItems([s["name"] + " (" + s["id"] + ")" for s in sources])
        self.name_edit = QtGui.QLineEdit(label)
        self.category_edit = QtGui.QLineEdit("General")
        self.host = QtGui.QComboBox()
        self.host.addItems(["all", "maya", "nuke", "houdini", "blender"])
        form.addRow("Library", self.library)
        form.addRow("Preset name", self.name_edit)
        form.addRow("Category", self.category_edit)
        form.addRow("Host", self.host)
        section_layout.addLayout(form)
        layout.addWidget(section)
        self.location = mark_secondary_text(QtGui.QLabel())
        self.location.setWordWrap(True)
        layout.addWidget(self.location)
        self.buttons = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Save | QtGui.QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        self.library.currentIndexChanged.connect(self.update_form)
        self.name_edit.textChanged.connect(self.update_form)
        self.category_edit.textChanged.connect(self.update_form)
        self.update_form()

    def update_form(self, *args):
        index = self.library.currentIndex()
        self.location.setText(self.sources[index]["remote_path"] if index >= 0 else "")
        valid = index >= 0 and bool(text_type(self.name_edit.text()).strip()) and bool(text_type(self.category_edit.text()).strip())
        self.buttons.button(QtGui.QDialogButtonBox.Save).setEnabled(valid)

    def accept(self):
        if self.buttons.button(QtGui.QDialogButtonBox.Save).isEnabled():
            QtGui.QDialog.accept(self)

    def values(self):
        return {"source": self.sources[self.library.currentIndex()],
                "label": text_type(self.name_edit.text()).strip(),
                "category": text_type(self.category_edit.text()).strip(),
                "dcc": text_type(self.host.currentText())}


class SourceEditDialog(QtGui.QDialog):
    def __init__(self, source=None, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setWindowTitle("Preset Library")
        self.source = source or {}
        layout = QtGui.QVBoxLayout(self)
        layout.setSpacing(SETTINGS_PAGE_SPACING)
        location_section, location_layout = build_simple_section("Library", parent=self)
        form = build_section_form()
        self.name_edit = QtGui.QLineEdit(self.source.get("name", ""))
        self.path_edit = QtGui.QLineEdit(self.source.get("remote_path", ""))
        path_row = QtGui.QWidget(self)
        path_layout = QtGui.QHBoxLayout(path_row)
        path_layout.setContentsMargins(0, 0, 0, 0)
        path_layout.addWidget(self.path_edit)
        browse = QtGui.QPushButton("Browse...")
        browse.clicked.connect(self.browse)
        path_layout.addWidget(browse)
        self.enabled = QtGui.QCheckBox("Enabled")
        self.enabled.setChecked(self.source.get("enabled", True))
        self.policy = QtGui.QComboBox()
        self.policy.addItems(["Manual", "On application start", "Periodically"])
        self.policy.setCurrentIndex(POLICIES.index(self.source.get("update_policy", "manual")))
        self.interval = QtGui.QSpinBox()
        self.interval.setRange(1, 10080)
        self.interval.setValue(self.source.get("interval_minutes", 60))
        self.interval.setSuffix(" min")
        form.addRow("Name", self.name_edit)
        form.addRow("Folder", path_row)
        form.addRow("", self.enabled)
        location_layout.addLayout(form)
        layout.addWidget(location_section)
        updates_section, updates_layout = build_simple_section("Updates", parent=self)
        updates_form = build_section_form()
        updates_form.addRow("Updates", self.policy)
        updates_form.addRow("Check interval", self.interval)
        updates_layout.addLayout(updates_form)
        layout.addWidget(updates_section)
        note = mark_secondary_text(QtGui.QLabel("Choose a trusted library folder. Changes are saved immediately."))
        note.setWordWrap(True)
        layout.addWidget(note)
        buttons = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Save | QtGui.QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def browse(self):
        path = QtGui.QFileDialog.getExistingDirectory(self, "Preset Library", self.path_edit.text())
        if path:
            self.path_edit.setText(path)

    def values(self):
        return {"name": text_type(self.name_edit.text()).strip(),
                "remote_path": text_type(self.path_edit.text()).strip(),
                "enabled": self.enabled.isChecked(),
                "update_policy": POLICIES[self.policy.currentIndex()],
                "interval_minutes": self.interval.value()}


class PresetLibraryPage(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.registry = SourceRegistry()
        self.service = SyncService(self.registry)
        self.job = None
        self.sources = []
        layout = QtGui.QVBoxLayout(self)
        layout.setContentsMargins(*SETTINGS_PAGE_MARGINS)
        layout.setSpacing(SETTINGS_PAGE_SPACING)
        layout.addWidget(build_page_header("Preset Library",
            "Default presets ship with the plugin. Add custom libraries by folder.", parent=self))
        scroll = QtGui.QScrollArea(self)
        configure_settings_scroll_area(scroll)
        content = QtGui.QWidget(scroll)
        content.setObjectName("SettingsScrollContent")
        content_layout = QtGui.QVBoxLayout(content)
        content_layout.setContentsMargins(*metrics.MARGINS_NONE)
        content_layout.setSpacing(metrics.SETTINGS_SECTION_SPACING)
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)
        libraries_section, libraries_layout = build_simple_section("Libraries", parent=content)
        self.list = QtGui.QListWidget()
        self.list.setMinimumHeight(metrics.LIST_ITEM_MIN_HEIGHT * 4)
        self.list.setMaximumHeight(metrics.LIST_ITEM_MIN_HEIGHT * 8)
        self.list.currentRowChanged.connect(self.selected)
        libraries_layout.addWidget(self.list)
        detail_section, detail_layout = build_simple_section("Selected Library", parent=content)
        self.detail = mark_status_text(QtGui.QLabel())
        self.detail.setWordWrap(True)
        self.detail.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        detail_layout.addWidget(self.detail)
        management_row = QtGui.QHBoxLayout()
        management_row.setSpacing(metrics.SETTINGS_ACTION_SPACING)
        sync_row = QtGui.QHBoxLayout()
        sync_row.setSpacing(metrics.SETTINGS_ACTION_SPACING)
        self.buttons = []
        for label, callback in (("Add Library", self.add), ("New Library", self.create_library), ("Edit", self.edit),
                                ("Remove", self.remove), ("Check now", self.check),
                                ("Sync now", self.sync)):
            button = QtGui.QPushButton(label)
            button.clicked.connect(callback)
            row = management_row if len(self.buttons) < 4 else sync_row
            row.addWidget(button)
            self.buttons.append(button)
        management_row.addStretch(1)
        sync_row.addStretch(1)
        libraries_layout.addLayout(management_row)
        detail_layout.addLayout(sync_row)
        note = mark_secondary_text(QtGui.QLabel("Updates apply on the next Toolbox open, Reload Config or editor Apply."))
        note.setWordWrap(True)
        detail_layout.addWidget(note)
        content_layout.addWidget(libraries_section)
        content_layout.addWidget(detail_section)
        content_layout.addStretch(1)
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.poll)
        self.refresh()

    def refresh(self):
        row = self.list.currentRow()
        self.sources = self.registry.sources()
        self.list.clear()
        self.list.addItem("Default (included with plugin)")
        for source in self.sources:
            self.list.addItem(source["name"] + ("" if source["enabled"] else " (disabled)"))
        self.list.setCurrentRow(max(0, min(row, len(self.sources))))

    def source(self):
        row = self.list.currentRow()
        return self.sources[row - 1] if 1 <= row <= len(self.sources) else None

    def selected(self, row):
        source = self.source()
        for button in self.buttons[2:]:
            button.setEnabled(source is not None and self.job is None)
        if source is None:
            self.detail.setText("Default\n{0}\nIncluded with the plugin. Definitions are read only; inserted copies are editable.".format(default_library_path()))
            return
        status = self.service.status(source["id"])
        last_sync = status.get("last_sync")
        last_sync = time.strftime("%Y-%m-%d %H:%M", time.localtime(last_sync)) if last_sync else "Never"
        self.detail.setText("{0}\nID: {1}\nStatus: {2}\nLocal / remote snapshot: {3} / {4}\nLast sync: {5}\n{6}{7}".format(
            source["remote_path"], source["id"], status["state"].replace("_", " "),
            (status.get("local_revision") or "None")[:12], (status.get("remote_revision") or "Unknown")[:12], last_sync,
            "Using local cache.\n" if status["using_cache"] else "Not installed.\n",
            status.get("error", "")))

    def start(self, action):
        if self.job is not None:
            return
        self.job = BackgroundJob(action)
        for button in self.buttons:
            button.setEnabled(False)
        self.detail.setText("Checking / synchronizing source...")
        self.timer.start()

    def poll(self):
        result = self.job.poll()
        if result is None:
            return
        self.timer.stop()
        self.job = None
        self.buttons[0].setEnabled(True)
        self.buttons[1].setEnabled(True)
        self.refresh()
        if not result["ok"]:
            self.detail.setText(result["error"])

    def edit_source(self, source=None):
        dialog = SourceEditDialog(source, self)
        if qt_exec(dialog) != QtGui.QDialog.Accepted:
            return
        values = dialog.values()
        registry, service = self.registry, self.service
        def install():
            if source is None:
                import os
                manifest = validate_manifest(read_json(os.path.join(values["remote_path"], MANIFEST)))
                values["id"] = manifest["id"]
                values["name"] = values["name"] or manifest["name"]
                if registry.get(values["id"]) is not None:
                    raise ValueError("This source is already connected; use Edit.")
            else:
                values["id"] = source["id"]
            registry.put(values)
            return service.check(values["id"], download=True)
        self.start(install)

    def add(self):
        self.edit_source()

    def create_library(self):
        folder = QtGui.QFileDialog.getExistingDirectory(self, "New Preset Library")
        if not folder:
            return
        name, accepted = QtGui.QInputDialog.getText(self, "New Preset Library", "Library name")
        if not accepted or not text_type(name).strip():
            return
        folder, name = text_type(folder), text_type(name).strip()
        registry, service = self.registry, self.service
        def create():
            from ..core.preset_library import publish_presets
            if os.path.exists(os.path.join(folder, MANIFEST)):
                raise ValueError("This folder already contains a library. Use Add Library.")
            source_id = "library-" + uuid.uuid4().hex
            publish_presets([], folder, source_id, name)
            registry.put({"id": source_id, "name": name, "remote_path": folder})
            return service.check(source_id, download=True)
        self.start(create)

    def edit(self):
        if self.source() is not None:
            self.edit_source(self.source())

    def remove(self):
        source = self.source()
        if source is not None:
            self.registry.remove(source["id"])
            self.refresh()

    def check(self):
        self.run_sync(False)

    def sync(self):
        self.run_sync(True)

    def run_sync(self, download):
        source = self.source()
        if source is not None:
            service = self.service
            source_id = source["id"]
            self.start(lambda: service.check(source_id, download=download))
