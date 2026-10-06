# -*- coding: utf-8 -*-
from __future__ import print_function

import copy
import uuid

from ..compat import HOST
from ..compat import QtCore
from ..compat import QtGui
from ..core.presets import build_preset_root
from ..core.presets import iter_presets
from ..pycompat import text_type
from ..style.palette import BORDER_PRESSED
from ..style.palette import LIST_BG
from ..style.palette import TEXT_PALETTE_GROUP
from .scroll_surface_frames import wrap_scroll_widget
from .managed_presets import (populate_managed_presets, target_address,
                              insert_reference, reference_tooltip, library_address, insert_library_preset,
                              BackgroundJob, SavePresetDialog)
from ..core.preset_references import local_copy
from ..core.preset_references import PresetResolver
from ..core.preset_sources import SourceRegistry
from ..style.builtin_icons import builtin_icon
from ..qt_compat import qt_exec
from ..core.editor_commands import ItemStateCommand


ROLE_PRESET_ID = QtCore.Qt.UserRole + 50


def _role_text(tree_item, role):
    if tree_item is None:
        return ""

    value = tree_item.data(
        0,
        role
    )
    try:
        value = value.toString()
    except Exception:
        pass

    return text_type(
        value or ""
    )


def _configure_palette_tree(tree):
    tree.setObjectName(
        "ParameterPalette"
    )
    tree.setHeaderHidden(
        True
    )
    tree.setRootIsDecorated(
        True
    )
    tree.setAlternatingRowColors(
        True
    )


def _populate_preset_tree(tree):
    default_group = QtGui.QTreeWidgetItem(["Default"])
    default_group.setFlags(default_group.flags() & ~QtCore.Qt.ItemIsSelectable)
    groups = {}
    group_order = []

    for preset in iter_presets(
        getattr(
            HOST,
            "key",
            ""
        )
    ):
        category = text_type(
            preset.get("category", "PRESETS") or "PRESETS"
        )
        group = groups.get(category)

        if group is None:
            group = QtGui.QTreeWidgetItem([
                category.title()
            ])
            group.setData(
                0,
                ROLE_PRESET_ID,
                ""
            )

            flags = group.flags()
            flags &= ~QtCore.Qt.ItemIsSelectable
            flags &= ~QtCore.Qt.ItemIsDragEnabled
            flags &= ~QtCore.Qt.ItemIsDropEnabled
            group.setFlags(
                flags
            )

            font = group.font(
                0
            )
            font.setBold(
                True
            )
            group.setFont(
                0,
                font
            )
            group.setForeground(
                0,
                QtGui.QBrush(
                    QtGui.QColor(
                        TEXT_PALETTE_GROUP
                    )
                )
            )

            groups[category] = group
            group_order.append(category)

        item = QtGui.QTreeWidgetItem([
            text_type(
                preset.get("label", preset.get("id", "Preset"))
            )
        ])
        item.setData(
            0,
            ROLE_PRESET_ID,
            text_type(
                preset.get("id", "")
            )
        )
        item.setToolTip(
            0,
            text_type(
                preset.get("description", "")
            )
        )
        group.addChild(
            item
        )

    for category in group_order:
        group = groups[category]
        default_group.addChild(group)
        group.setExpanded(
            True
        )
    tree.addTopLevelItem(default_group)
    default_group.setExpanded(True)
    for group in groups.values():
        group.setExpanded(True)


def _filter_preset_tree(tree, value):
    query = text_type(
        value or ""
    ).strip().lower()

    def visit(item, inherited=False):
        label = text_type(item.text(0)).lower()
        tooltip = text_type(item.toolTip(0)).lower()
        preset_id = _role_text(item, ROLE_PRESET_ID).lower()
        own = not query or query in label or query in tooltip or query in preset_id
        matched = own or inherited
        visible_children = False
        for index in range(item.childCount()):
            visible_children = visit(item.child(index), matched) or visible_children
        visible = matched or visible_children
        item.setHidden(not visible)
        if query and visible_children:
            item.setExpanded(True)
        return visible
    for index in range(tree.topLevelItemCount()):
        visit(tree.topLevelItem(index))


def _insert_preset(
    editor,
    preset_item,
    column=0
):
    preset_id = _role_text(
        preset_item,
        ROLE_PRESET_ID
    )
    if not preset_id:
        return None

    source = build_preset_root(
        preset_id
    )
    if source is None:
        return None

    editor.sync_working_from_tree()
    clone = editor._clone_data(
        source,
        editor._used_names()
    )
    tree_item = editor._insert_cloned_tree_item(
        clone,
        sibling=False
    )
    editor.tree.setCurrentItem(
        tree_item
    )

    try:
        tree_item.setExpanded(
            True
        )
    except Exception:
        pass

    editor.fix_tree_structure()
    editor.tree_changed()
    return tree_item


class PresetEditorMixin(object):

    def __init__(self, *args, **kwargs):
        self._preset_save_job = None
        # Catalog updates are visible when the editor is opened. Runtime
        # changes only when the user explicitly applies this staged document.
        self.preset_resolver = PresetResolver(SourceRegistry())
        super(PresetEditorMixin, self).__init__(*args, **kwargs)

    def apply_changes(self):
        old = self.toolbox.preset_resolver
        self.toolbox.preset_resolver = self.preset_resolver
        try:
            result = super(PresetEditorMixin, self).apply_changes()
        except Exception:
            self.toolbox.preset_resolver = old
            raise
        if result is False:
            self.toolbox.preset_resolver = old
        return result

    def make_tree_item(self, data):
        item = super(PresetEditorMixin, self).make_tree_item(data)
        if data.get("kind") == "reference":
            tooltip, broken = reference_tooltip(data, self.preset_resolver)
            item.setIcon(0, builtin_icon("close-circle" if broken else "reference"))
            item.setToolTip(0, tooltip)
        return item

    def show_preset_context_menu(self, point):
        item = self.preset_palette.itemAt(point)
        if library_address(item) is not None and target_address(item) is None:
            menu = QtGui.QMenu(self.preset_palette)
            action = menu.addAction("Create References")
            if qt_exec(menu, self.preset_palette.viewport().mapToGlobal(point)) == action:
                self._call_tree_action("Create References", insert_library_preset, item)
            return
        if target_address(item) is None:
            return
        menu = QtGui.QMenu(self.preset_palette)
        reference_action = menu.addAction("Create Reference")
        if qt_exec(menu, self.preset_palette.viewport().mapToGlobal(point)) == reference_action:
            self._call_tree_action("Create Reference", insert_reference, item)

    def extend_tree_context_menu(self, menu, item):
        actions = super(PresetEditorMixin, self).extend_tree_context_menu(menu, item)
        menu.addSeparator()
        save = menu.addAction("Save Selected as Preset...")
        save.setEnabled(item is not None and self._preset_save_job is None)
        actions.append((save, self.save_selected_preset))
        return actions

    def show_tree_context_menu(self, point):
        tree_item = self.tree.itemAt(point)
        data = self.item_cache.get(self.item_data(tree_item, QtCore.Qt.UserRole + 1)) if tree_item else None
        if data is None or data.get("kind") != "reference":
            return super(PresetEditorMixin, self).show_tree_context_menu(point)
        self.tree.setCurrentItem(tree_item)
        menu = QtGui.QMenu(self.tree)
        reveal = menu.addAction("Reveal in Presets")
        resolve = menu.addAction("Resolve")
        convert = menu.addAction("Convert to Local Copy")
        _, broken = reference_tooltip(data, self.preset_resolver)
        convert.setEnabled(not broken)
        menu.addSeparator()
        remove = menu.addAction("Remove Reference")
        extra_actions = self.extend_tree_context_menu(menu, tree_item)
        action = qt_exec(menu, self.tree.viewport().mapToGlobal(point))
        if action == remove:
            self.delete_selected()
        elif action == resolve:
            self.selection_changed(tree_item, tree_item)
        elif action == convert:
            self._call_tree_action("Convert Reference", _convert_reference, data["id"])
        elif any(action == extra_action for extra_action, callback in extra_actions):
            for extra_action, callback in extra_actions:
                if action == extra_action:
                    callback()
                    break
        elif action == reveal:
            target = data["props"]
            address = [target["source"], target["preset"], target["parameter"]]
            self.palette_tabs.setCurrentIndex(1)
            self.palette_filter.clear()
            def reveal_item(item):
                if target_address(item) == address:
                    return item
                for i in range(item.childCount()):
                    found = reveal_item(item.child(i))
                    if found is not None:
                        return found
                return None
            for index in range(self.preset_palette.topLevelItemCount()):
                found = reveal_item(self.preset_palette.topLevelItem(index))
                if found is not None:
                    parent = found.parent()
                    while parent is not None:
                        parent.setExpanded(True)
                        parent = parent.parent()
                    self.preset_palette.setCurrentItem(found)
                    self.preset_palette.scrollToItem(found)
                    return

    def build_ui(self):
        super(PresetEditorMixin, self).build_ui()
        self._install_preset_palette()

    def _install_preset_palette(self):
        items_surface = getattr(
            self,
            "palette_scroll_frame",
            None
        )
        if items_surface is None:
            items_surface = self.palette

        left = items_surface.parentWidget()
        if left is None:
            return

        left_layout = left.layout()
        if left_layout is None:
            return

        palette_index = left_layout.indexOf(
            items_surface
        )
        if palette_index < 0:
            palette_index = 1

        self.palette_tabs = QtGui.QTabWidget(
            left
        )
        self.palette_tabs.setObjectName(
            "CreatePaletteTabs"
        )

        items_page = QtGui.QWidget(
            self.palette_tabs
        )
        items_layout = QtGui.QVBoxLayout(
            items_page
        )
        items_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )
        items_layout.setSpacing(
            0
        )

        left_layout.removeWidget(
            items_surface
        )
        items_surface.setParent(
            items_page
        )
        items_layout.addWidget(
            items_surface
        )

        presets_page = QtGui.QWidget(
            self.palette_tabs
        )
        presets_layout = QtGui.QVBoxLayout(
            presets_page
        )
        presets_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )
        presets_layout.setSpacing(
            0
        )

        self.preset_palette = QtGui.QTreeWidget(
            presets_page
        )
        _configure_palette_tree(
            self.preset_palette
        )
        try:
            self.preset_palette.setIndentation(
                self.palette.indentation()
            )
        except Exception:
            pass
        _populate_preset_tree(
            self.preset_palette
        )
        populate_managed_presets(self, self.preset_palette)
        self.preset_palette.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.preset_palette.customContextMenuRequested.connect(self.show_preset_context_menu)
        self.preset_palette.itemDoubleClicked.connect(
            self.create_from_preset
        )
        presets_layout.addWidget(
            self.preset_palette
        )
        self.preset_scroll_frame = wrap_scroll_widget(
            self.preset_palette,
            background=LIST_BG,
            border=BORDER_PRESSED
        )

        self.palette_tabs.addTab(
            items_page,
            "Items"
        )
        self.palette_tabs.addTab(
            presets_page,
            "Presets"
        )

        left_layout.insertWidget(
            palette_index,
            self.palette_tabs,
            1
        )

        self.palette_tabs.currentChanged.connect(
            self._palette_tab_changed
        )
        self._palette_tab_changed(
            self.palette_tabs.currentIndex()
        )

    def save_selected_preset(self):
        if self._preset_save_job is not None:
            return
        self.sync_working_from_tree()
        item = self.item_cache.get(self.current_item_id)
        if item is None:
            QtGui.QMessageBox.information(self, "Save Preset", "Select an item in Existing Parameters first.")
            return
        sources = [s for s in self.preset_resolver.sources.values() if s["enabled"]]
        if not sources:
            QtGui.QMessageBox.information(self, "Save Preset", "Create or connect a custom library in Settings > Preset Library first.")
            return
        dialog = SavePresetDialog(sources, item["ui"]["label"], self)
        accepted = qt_exec(dialog) == QtGui.QDialog.Accepted
        options = dialog.values() if accepted else None
        dialog.deleteLater()
        if not accepted:
            return
        source = options["source"]
        root = copy.deepcopy(item)
        def materialize(node):
            if node["kind"] == "reference":
                return local_copy(node, self.preset_resolver)
            if "items" in node:
                node["items"] = [materialize(child) for child in node["items"]]
            return node
        try:
            root = materialize(root)
        except (ValueError, TypeError, KeyError) as exc:
            QtGui.QMessageBox.warning(self, "Save Preset", text_type(exc))
            return
        preset = {"id": "preset-" + uuid.uuid4().hex, "label": options["label"],
                  "category": options["category"], "dcc": options["dcc"], "root": root}
        registry = self.preset_resolver.registry
        def publish():
            from ..core.preset_library import publish_presets
            from ..core.preset_sync import SyncService
            publish_presets([preset], source["remote_path"], source["id"], source["name"], merge=True)
            service = SyncService(registry)
            status = service.check(source["id"], download=True)
            if status["state"] != "up_to_date":
                raise ValueError("Preset published, but local sync failed: " + status.get("error", status["state"]))
            package = service.installed(source["id"])
            return next(p for p in package["presets"] if p["id"] == preset["id"])
        self._preset_save_job = BackgroundJob(publish)
        self._preset_save_timer = QtCore.QTimer(self)
        def poll():
            result = self._preset_save_job.poll()
            if result is None:
                return
            self._preset_save_timer.stop()
            self._preset_save_timer.deleteLater()
            self._preset_save_job = None
            if not result["ok"]:
                QtGui.QMessageBox.warning(self, "Save Preset", result["error"])
                return
            self._reveal_saved_preset(source["id"], result["value"])
        self._preset_save_timer.timeout.connect(poll)
        self._preset_save_timer.start(100)

    def _reveal_saved_preset(self, source_id, preset):
        # Add only the newly published definition. Existing references retain
        # their snapshots, including when Apply has shared this resolver.
        resolver = copy.copy(self.preset_resolver)
        resolver.packages = dict(resolver.packages)
        package = dict(resolver.packages.get(source_id, {}))
        package["presets"] = list(package.get("presets", [])) + [preset]
        resolver.packages[source_id] = package
        self.preset_resolver = resolver
        self.preset_palette.clear()
        _populate_preset_tree(self.preset_palette)
        populate_managed_presets(self, self.preset_palette)
        self.palette_tabs.setCurrentIndex(1)
        self.palette_filter.clear()
        def find(item):
            if library_address(item) == [source_id, preset["id"]]:
                return item
            for index in range(item.childCount()):
                match = find(item.child(index))
                if match is not None:
                    return match
            return None
        for index in range(self.preset_palette.topLevelItemCount()):
            match = find(self.preset_palette.topLevelItem(index))
            if match is not None:
                self.preset_palette.setCurrentItem(match)
                self.preset_palette.scrollToItem(match)
                self.status.setText("Preset saved.")
                return
        self.status.setText("Preset saved for host: " + preset.get("dcc", "all"))

    def _palette_tab_changed(self, index):
        placeholder = (
            "Filter presets..."
            if index == 1
            else "Filter items..."
        )
        try:
            self.palette_filter.setPlaceholderText(
                placeholder
            )
        except Exception:
            pass

        self.filter_palette(
            text_type(
                self.palette_filter.text()
            )
        )

    def filter_palette(self, value):
        tabs = getattr(
            self,
            "palette_tabs",
            None
        )
        if (
            tabs is None or
            tabs.currentIndex() == 0
        ):
            return super(PresetEditorMixin, self).filter_palette(value
            )

        return _filter_preset_tree(
            self.preset_palette,
            value
        )

    def create_from_preset(
        self,
        preset_item,
        column=0
    ):
        if library_address(preset_item) is not None and target_address(preset_item) is None:
            return self._call_tree_action("Create References", insert_library_preset, preset_item, column)
        if target_address(preset_item) is not None:
            return self._call_tree_action("Create Reference", insert_reference, preset_item, column)
        callback = getattr(
            self,
            "_call_tree_action",
            None
        )
        if callback is not None:
            return callback(
                "Insert Preset",
                _insert_preset,
                preset_item,
                column
            )

        return _insert_preset(
            self,
            preset_item,
            column
        )


def _convert_reference(editor, item_id):
    editor.commit_history()
    item = editor.item_cache[item_id]
    before = editor.document_controller.item_state(item)
    converted = local_copy(item, editor.preset_resolver)
    item.clear()
    item.update(converted)
    after = editor.document_controller.item_state(item)
    editor.command_history.push_applied(ItemStateCommand(
        item_id, before, after, label="Convert Reference",
        selection_before=item_id, selection_after=item_id))
    editor.populate_tree()
    editor.tree.setCurrentItem(editor.tree_item_by_id(item_id))
    editor._sync_property_baseline()
    editor.status.setText("Modified — Apply or Accept to save.")


def build_preset_interface_editor_class(base_class):
    return type("InterfaceEditor", (PresetEditorMixin, base_class), {})


__all__ = [
    "PresetEditorMixin",
    "ROLE_PRESET_ID",
    "build_preset_interface_editor_class",
]
