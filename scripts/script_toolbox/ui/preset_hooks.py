# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore
from ..compat import QtGui
from ..core.presets import build_preset_root
from ..core.presets import iter_presets
from ..pycompat import text_type
from ..style.palette import BORDER_PRESSED
from ..style.palette import LIST_BG
from ..style.palette import TEXT_PALETTE_GROUP
from .scroll_surface_frames import wrap_scroll_widget


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

    for preset in iter_presets():
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


def build_preset_interface_editor_class(base_class):
    """Add Items/Presets tabs to the existing Create Parameters pane."""

    class PresetInterfaceEditor(base_class):

        def build_ui(self):
            base_class.build_ui(
                self
            )
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
                return base_class.filter_palette(
                    self,
                    value
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

    PresetInterfaceEditor.__name__ = "InterfaceEditor"
    return PresetInterfaceEditor


__all__ = [
    "ROLE_PRESET_ID",
    "build_preset_interface_editor_class",
]
