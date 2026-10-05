# -*- coding: utf-8 -*-
from __future__ import print_function

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
                              insert_reference, reference_tooltip)
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
                category
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
        tree.addTopLevelItem(
            group
        )
        group.setExpanded(
            True
        )


def _filter_preset_tree(tree, value):
    query = text_type(
        value or ""
    ).strip().lower()

    for group_index in range(
        tree.topLevelItemCount()
    ):
        group = tree.topLevelItem(
            group_index
        )
        visible_children = 0

        for child_index in range(
            group.childCount()
        ):
            child = group.child(
                child_index
            )
            label = text_type(
                child.text(0)
            ).lower()
            tooltip = text_type(
                child.toolTip(0)
            ).lower()
            preset_id = _role_text(
                child,
                ROLE_PRESET_ID
            ).lower()

            visible = (
                not query or
                query in label or
                query in tooltip or
                query in preset_id
            )
            child.setHidden(
                not visible
            )

            if visible:
                visible_children += 1

        group.setHidden(
            visible_children == 0
        )

        if query and visible_children:
            group.setExpanded(
                True
            )


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
        if target_address(item) is None:
            return
        menu = QtGui.QMenu(self.preset_palette)
        reference_action = menu.addAction("Create Reference")
        if qt_exec(menu, self.preset_palette.viewport().mapToGlobal(point)) == reference_action:
            self._call_tree_action("Create Reference", insert_reference, item)

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
        action = qt_exec(menu, self.tree.viewport().mapToGlobal(point))
        if action == remove:
            self.delete_selected()
        elif action == resolve:
            self.selection_changed(tree_item, tree_item)
        elif action == convert:
            self._call_tree_action("Convert Reference", _convert_reference, data["id"])
        elif action == reveal:
            target = data["props"]
            address = [target["source"], target["preset"], target["parameter"]]
            self.palette_tabs.setCurrentIndex(1)
            self.palette_filter.clear()
            for index in range(self.preset_palette.topLevelItemCount()):
                group = self.preset_palette.topLevelItem(index)
                for child_index in range(group.childCount()):
                    item = group.child(child_index)
                    if target_address(item) == address:
                        self.preset_palette.setCurrentItem(item)
                        self.preset_palette.scrollToItem(item)
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
