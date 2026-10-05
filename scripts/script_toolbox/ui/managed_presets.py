# -*- coding: utf-8 -*-
"""Qt presentation of managed parameters; network work never runs on Qt."""
from __future__ import print_function

import threading
import time
try:
    import queue
except ImportError:
    import Queue as queue

from ..compat import HOST, QtCore, QtGui
from ..core.preset_references import iter_targets
from ..core.preset_sources import SourceRegistry, POLICIES
from ..core.preset_sync import SyncService, MANIFEST, read_json, validate_manifest
from ..pycompat import text_type
from ..qt_compat import qt_exec
from ..style.metrics import SETTINGS_PAGE_MARGINS, SETTINGS_PAGE_SPACING
from .settings_components import build_page_header, build_section_form

ROLE_TARGET = QtCore.Qt.UserRole + 51


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
        package = resolver.packages.get(source_id)
        if package is not None:
            for preset in package["presets"]:
                dcc = preset.get("dcc", "all")
                if dcc not in ("all", getattr(HOST, "key", "")):
                    continue
                for target in iter_targets(preset["root"]):
                    item = QtGui.QTreeWidgetItem([target["ui"]["label"]])
                    item.setData(0, ROLE_TARGET, "{0}/{1}/{2}".format(
                        source_id, preset["id"], target["id"]))
                    item.setToolTip(0, "{0} / {1} / {2}\nRead-only definition".format(
                        source["name"], preset.get("label", preset["id"]), target["name"]))
                    group.addChild(item)
        else:
            group.setToolTip(0, "Not installed. Synchronize this source in Settings.")
        tree.addTopLevelItem(group)
        group.setExpanded(True)


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


class SourceEditDialog(QtGui.QDialog):
    def __init__(self, source=None, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setWindowTitle("Preset Source")
        self.source = source or {}
        layout = QtGui.QVBoxLayout(self)
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
        form.addRow("Updates", self.policy)
        form.addRow("Check interval", self.interval)
        layout.addLayout(form)
        note = QtGui.QLabel("The source ID is read from toolbox-source.json.\n"
                            "Published presets may contain executable scripts.")
        note.setWordWrap(True)
        layout.addWidget(note)
        buttons = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Save | QtGui.QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def browse(self):
        path = QtGui.QFileDialog.getExistingDirectory(self, "Preset Source", self.path_edit.text())
        if path:
            self.path_edit.setText(path)

    def values(self):
        return {"name": text_type(self.name_edit.text()).strip(),
                "remote_path": text_type(self.path_edit.text()).strip(),
                "enabled": self.enabled.isChecked(),
                "update_policy": POLICIES[self.policy.currentIndex()],
                "interval_minutes": self.interval.value()}


class PresetSourcesPage(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.registry = SourceRegistry()
        self.service = SyncService(self.registry)
        self.job = None
        self.sources = []
        layout = QtGui.QVBoxLayout(self)
        layout.setContentsMargins(*SETTINGS_PAGE_MARGINS)
        layout.setSpacing(SETTINGS_PAGE_SPACING)
        layout.addWidget(build_page_header("Preset Sources",
            "Read-only studio presets cached locally. Source changes are saved immediately.", parent=self))
        self.list = QtGui.QListWidget()
        self.list.currentRowChanged.connect(self.selected)
        layout.addWidget(self.list, 1)
        self.detail = QtGui.QLabel()
        self.detail.setWordWrap(True)
        self.detail.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        layout.addWidget(self.detail)
        row = QtGui.QHBoxLayout()
        self.buttons = []
        for label, callback in (("Add Source", self.add), ("Edit", self.edit),
                                ("Remove", self.remove), ("Check now", self.check),
                                ("Sync now", self.sync)):
            button = QtGui.QPushButton(label)
            button.clicked.connect(callback)
            row.addWidget(button)
            self.buttons.append(button)
        layout.addLayout(row)
        note = QtGui.QLabel("Updates apply on the next Toolbox open, Reload Config or editor Apply.")
        note.setWordWrap(True)
        layout.addWidget(note)
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.poll)
        self.refresh()

    def refresh(self):
        row = self.list.currentRow()
        self.sources = self.registry.sources()
        self.list.clear()
        for source in self.sources:
            self.list.addItem(source["name"] + ("" if source["enabled"] else " (disabled)"))
        if self.sources:
            self.list.setCurrentRow(max(0, min(row, len(self.sources) - 1)))
        else:
            self.selected(-1)

    def source(self):
        row = self.list.currentRow()
        return self.sources[row] if 0 <= row < len(self.sources) else None

    def selected(self, row):
        source = self.source()
        for button in self.buttons[1:]:
            button.setEnabled(source is not None and self.job is None)
        if source is None:
            self.detail.setText("No source selected.")
            return
        status = self.service.status(source["id"])
        last_sync = status.get("last_sync")
        last_sync = time.strftime("%Y-%m-%d %H:%M", time.localtime(last_sync)) if last_sync else "Never"
        self.detail.setText("{0}\nID: {1}\nStatus: {2}\nLocal / remote revision: {3} / {4}\nLast sync: {5}\n{6}{7}".format(
            source["remote_path"], source["id"], status["state"].replace("_", " "),
            status.get("local_revision"), status.get("remote_revision", "Unknown"), last_sync,
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
