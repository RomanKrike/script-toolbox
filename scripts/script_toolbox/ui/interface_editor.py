# -*- coding: utf-8 -*-
from __future__ import print_function

import copy
import os

from ..compat import HOST
from ..compat import QtCore
from ..compat import QtGui
from ..constants import EDITOR_OBJECT_NAME
from ..core.config import config_path
from ..core.config import export_config
from ..core.config import import_config
from ..model import create_item
from ..model import normalize_document
from ..model import walk_items
from ..model.item_builtins import register_builtin_items
from ..model.item_registry import ITEM_TYPES
from ..model.items import new_id
from ..model.items import sanitize_name
from ..pycompat import text_type
from ..style import STYLE
from ..style import metrics
from ..style.palette import TEXT_PALETTE_GROUP
from ..style.palette import WINDOW_BG
from .editor_search import filter_existing_parameters as filter_editor_structure
from .icon_button import ICON_BUTTON_COMPACT
from .icon_button import create_icon_button
from .interface_tree import ExistingInterfaceTree
from .item_palette import palette_groups
from .layout_editor_adapter import create_layout_from_palette
from .layout_editor_adapter import fix_layout_tree_structure
from .layout_editor_adapter import insert_layout_cloned_tree_item
from .layout_editor_adapter import make_layout_tree_item
from .layout_editor_adapter import sync_layout_working_from_tree
from .layout_helpers import configure_layout
from .layout_helpers import set_layout_margins
from .properties import create_editor
from .search_field import SearchField


ROLE_KIND = QtCore.Qt.UserRole
ROLE_ID = QtCore.Qt.UserRole + 1

_EDITOR_CLIPBOARD = None


def _definition(kind):
    register_builtin_items()
    return ITEM_TYPES.get(text_type(kind or "").lower())


def _is_section(kind):
    definition = _definition(kind)
    return bool(definition and definition.has_capability("section"))


def _is_container(kind):
    definition = _definition(kind)
    return bool(definition and definition.is_container)


def _default_section_kind():
    register_builtin_items()
    for definition in ITEM_TYPES.creatable():
        if definition.has_capability("section"):
            return definition.kind
    raise RuntimeError("No creatable section Item type is registered.")


def _item_label(data):
    ui = data.get("ui", {}) if isinstance(data, dict) else {}
    if not isinstance(ui, dict):
        ui = {}
    return text_type(ui.get("label", data.get("name", "")))


class InterfaceEditor(QtGui.QDialog):

    def __init__(
        self,
        toolbox,
        parent=None
    ):
        QtGui.QDialog.__init__(
            self,
            parent
        )

        self.toolbox = toolbox
        self.working = copy.deepcopy(
            toolbox.config
        )
        self.item_cache = {}

        self.current_property_editor = None
        self.current_item_id = None

        self.clipboard_item = _EDITOR_CLIPBOARD
        self.undo_stack = []
        self.redo_stack = []
        self._history_current = copy.deepcopy(
            self.working
        )
        self._history_restoring = False
        self.history_timer = QtCore.QTimer(
            self
        )
        self.history_timer.setSingleShot(True)
        self.history_timer.setInterval(300)
        self.history_timer.timeout.connect(
            self.commit_history
        )

        self.setObjectName(
            EDITOR_OBJECT_NAME
        )
        self.setWindowTitle(
            "Edit Parameter Interface - {0}".format(
                HOST.display_name
            )
        )
        self.resize(
            1240,
            720
        )
        self.setMinimumSize(
            980,
            600
        )
        self.setStyleSheet(
            STYLE
        )

        self.build_ui()
        self.populate_tree()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def build_ui(self):
        root = QtGui.QVBoxLayout(
            self
        )
        configure_layout(
            root,
            margins=metrics.EDITOR_ROOT_MARGINS,
            spacing=metrics.EDITOR_ROOT_SPACING
        )

        heading = QtGui.QLabel(
            "Edit Parameter Interface  —  Script Toolbox  —  {0}".format(
                HOST.display_name
            )
        )
        heading.setObjectName(
            "DialogHeading"
        )
        root.addWidget(
            heading
        )

        splitter = QtGui.QSplitter(
            QtCore.Qt.Horizontal
        )
        splitter.setHandleWidth(
            metrics.EDITOR_SPLITTER_HANDLE_WIDTH
        )
        splitter.setChildrenCollapsible(
            False
        )
        root.addWidget(
            splitter,
            1
        )

        self.search_fields = {}

        left = QtGui.QWidget()
        left.setObjectName(
            "EditorPane"
        )
        left_layout = QtGui.QVBoxLayout(
            left
        )
        configure_layout(
            left_layout,
            margins=metrics.EDITOR_PANE_MARGINS,
            spacing=metrics.EDITOR_PANE_SPACING
        )

        left_title = QtGui.QLabel(
            "Create Parameters"
        )
        left_title.setObjectName(
            "PaneTitle"
        )
        left_layout.addWidget(
            left_title
        )

        self.palette = QtGui.QTreeWidget()
        self.palette.setObjectName(
            "ParameterPalette"
        )
        self.palette.setHeaderHidden(
            True
        )
        self.palette.setRootIsDecorated(
            True
        )
        self.palette.setIndentation(
            metrics.EDITOR_PALETTE_INDENT
        )
        self.palette.setAlternatingRowColors(
            True
        )

        for group_label, entries in palette_groups():
            group_item = QtGui.QTreeWidgetItem([
                group_label
            ])

            group_item.setData(
                0,
                ROLE_KIND,
                ""
            )

            group_flags = group_item.flags()
            group_flags &= ~QtCore.Qt.ItemIsSelectable
            group_flags &= ~QtCore.Qt.ItemIsDragEnabled
            group_flags &= ~QtCore.Qt.ItemIsDropEnabled
            group_item.setFlags(
                group_flags
            )

            group_font = group_item.font(
                0
            )
            group_font.setBold(
                True
            )
            group_item.setFont(
                0,
                group_font
            )
            group_item.setForeground(
                0,
                QtGui.QBrush(
                    QtGui.QColor(
                        TEXT_PALETTE_GROUP
                    )
                )
            )

            self.palette.addTopLevelItem(
                group_item
            )

            for label, kind, tooltip in entries:
                item = QtGui.QTreeWidgetItem([
                    label
                ])
                item.setData(
                    0,
                    ROLE_KIND,
                    kind
                )
                item.setToolTip(
                    0,
                    tooltip
                )
                group_item.addChild(
                    item
                )

            group_item.setExpanded(
                True
            )

        self.palette.itemDoubleClicked.connect(
            self.create_from_palette
        )

        left_layout.addWidget(
            self.palette,
            1
        )

        self.palette_filter = SearchField(
            "Filter parameters...",
            parent=left
        )
        self.palette_filter.textChanged.connect(
            self.filter_palette
        )
        self.palette_search_control = self.palette_filter
        self.search_fields[
            "palette"
        ] = self.palette_filter
        left_layout.addWidget(
            self.palette_filter
        )

        splitter.addWidget(
            left
        )

        center = QtGui.QWidget()
        center.setObjectName(
            "EditorPane"
        )
        center_layout = QtGui.QVBoxLayout(
            center
        )
        configure_layout(
            center_layout,
            margins=metrics.EDITOR_PANE_MARGINS,
            spacing=metrics.EDITOR_PANE_SPACING
        )

        toolbar = QtGui.QHBoxLayout()
        toolbar.setSpacing(
            metrics.TOOLBAR_SPACING
        )

        center_title = QtGui.QLabel(
            "Existing Parameters"
        )
        center_title.setObjectName(
            "PaneTitle"
        )
        toolbar.addWidget(
            center_title
        )
        toolbar.addStretch(
            1
        )

        self.structure_toolbar_buttons = {}
        for icon_name, tooltip, callback in (
            ("undo", "Undo (Ctrl+Z)", self.undo),
            ("redo", "Redo (Ctrl+Y)", self.redo),
            ("copy", "Copy (Ctrl+C)", self.copy_selected),
            ("paste", "Paste (Ctrl+V)", self.paste_selected),
            ("up", "Move Up", lambda: self.move_selected(-1)),
            ("down", "Move Down", lambda: self.move_selected(1)),
            ("delete", "Delete", self.delete_selected),
        ):
            button = create_icon_button(
                icon_name,
                tooltip,
                callback,
                parent=self,
                preset=ICON_BUTTON_COMPACT
            )
            self.structure_toolbar_buttons[
                icon_name
            ] = button
            toolbar.addWidget(
                button
            )

        center_layout.addLayout(
            toolbar
        )

        self.tree = ExistingInterfaceTree(
            self
        )
        self.tree.setAlternatingRowColors(
            True
        )
        self.tree.setUniformRowHeights(
            True
        )
        self.tree.setIndentation(
            metrics.EDITOR_TREE_INDENT
        )
        self.tree.currentItemChanged.connect(
            self.selection_changed
        )
        self.tree.setContextMenuPolicy(
            QtCore.Qt.CustomContextMenu
        )
        self.tree.customContextMenuRequested.connect(
            self.show_tree_context_menu
        )

        self.shortcuts = []
        for sequence, callback in (
            ("Ctrl+Z", self.undo),
            ("Ctrl+Y", self.redo),
            ("Ctrl+Shift+Z", self.redo),
            ("Ctrl+C", self.copy_selected),
            ("Ctrl+V", self.paste_selected),
            ("Ctrl+D", self.duplicate_selected),
            ("Delete", self.delete_selected),
        ):
            shortcut = QtGui.QShortcut(
                QtGui.QKeySequence(sequence),
                self.tree
            )
            try:
                shortcut.setContext(
                    QtCore.Qt.WidgetWithChildrenShortcut
                )
            except Exception:
                pass
            shortcut.activated.connect(callback)
            self.shortcuts.append(shortcut)

        center_layout.addWidget(
            self.tree,
            1
        )

        self.existing_filter = SearchField(
            "Filter existing parameters...",
            parent=center
        )
        self.existing_filter.textChanged.connect(
            self.filter_existing_parameters
        )
        self.existing_search_control = self.existing_filter
        self.search_fields[
            "structure"
        ] = self.existing_filter
        center_layout.addWidget(
            self.existing_filter
        )

        splitter.addWidget(
            center
        )

        right = QtGui.QWidget()
        right.setObjectName(
            "EditorPane"
        )
        right_layout = QtGui.QVBoxLayout(
            right
        )
        configure_layout(
            right_layout,
            margins=metrics.EDITOR_PANE_MARGINS,
            spacing=metrics.EDITOR_PANE_SPACING
        )

        right_title = QtGui.QLabel(
            "Parameter Description"
        )
        right_title.setObjectName(
            "PaneTitle"
        )
        right_layout.addWidget(
            right_title
        )

        self.property_scroll = QtGui.QScrollArea()
        self.property_scroll.setObjectName(
            "PropertyScroll"
        )
        self.property_scroll.setWidgetResizable(
            True
        )
        self.property_scroll.setFrameShape(
            QtGui.QFrame.NoFrame
        )
        self.property_scroll.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff
        )

        try:
            viewport = self.property_scroll.viewport()
            viewport.setObjectName("PropertyViewport")
            viewport_palette = viewport.palette()
            viewport_palette.setColor(
                QtGui.QPalette.Window,
                QtGui.QColor(WINDOW_BG)
            )
            viewport_palette.setColor(
                QtGui.QPalette.Base,
                QtGui.QColor(WINDOW_BG)
            )
            viewport.setPalette(viewport_palette)
            viewport.setAutoFillBackground(True)
        except Exception:
            pass

        self.property_host = QtGui.QWidget()
        self.property_host.setObjectName(
            "PropertyHost"
        )
        try:
            host_palette = self.property_host.palette()
            host_palette.setColor(
                QtGui.QPalette.Window,
                QtGui.QColor(WINDOW_BG)
            )
            host_palette.setColor(
                QtGui.QPalette.Base,
                QtGui.QColor(WINDOW_BG)
            )
            self.property_host.setPalette(host_palette)
            self.property_host.setAutoFillBackground(True)
        except Exception:
            pass
        self.property_layout = QtGui.QVBoxLayout(
            self.property_host
        )
        set_layout_margins(
            self.property_layout,
            metrics.EDITOR_PROPERTY_HOST_MARGINS
        )
        self.property_scroll.setWidget(
            self.property_host
        )
        right_layout.addWidget(
            self.property_scroll,
            1
        )

        splitter.addWidget(
            right
        )

        splitter.setSizes([
            220,
            420,
            580
        ])

        bottom = QtGui.QHBoxLayout()
        bottom.setSpacing(
            metrics.EDITOR_BOTTOM_SPACING
        )

        import_button = self._icon_button(
            "import",
            "Import Toolbox Settings",
            self.import_settings
        )
        export_button = self._icon_button(
            "export",
            "Export Toolbox Settings",
            self.export_settings
        )

        bottom.addWidget(
            import_button
        )
        bottom.addWidget(
            export_button
        )
        bottom.addSpacing(
            metrics.EDITOR_BOTTOM_GROUP_SPACING
        )

        self.status = QtGui.QLabel(
            "Changes are staged until Apply or Accept."
        )
        self.status.setObjectName(
            "EditorStatus"
        )
        bottom.addWidget(
            self.status
        )
        bottom.addStretch(
            1
        )

        apply_button = QtGui.QPushButton(
            "Apply"
        )
        apply_button.setMinimumWidth(
            metrics.EDITOR_ACTION_BUTTON_MIN_WIDTH
        )
        apply_button.clicked.connect(
            self.apply_changes
        )

        accept_button = QtGui.QPushButton(
            "Accept"
        )
        accept_button.setObjectName(
            "AcceptButton"
        )
        accept_button.setMinimumWidth(
            metrics.EDITOR_ACTION_BUTTON_MIN_WIDTH
        )
        accept_button.clicked.connect(
            self.accept_changes
        )

        cancel_button = QtGui.QPushButton(
            "Cancel"
        )
        cancel_button.setMinimumWidth(
            metrics.EDITOR_ACTION_BUTTON_MIN_WIDTH
        )
        cancel_button.clicked.connect(
            self.reject
        )

        bottom.addWidget(
            apply_button
        )
        bottom.addWidget(
            accept_button
        )
        bottom.addWidget(
            cancel_button
        )

        root.addLayout(
            bottom
        )

        self.show_empty_properties()

    def _icon_button(
        self,
        icon_name,
        tooltip,
        callback
    ):
        return create_icon_button(
            icon_name,
            tooltip,
            callback,
            parent=self,
            preset=ICON_BUTTON_COMPACT
        )

    # ------------------------------------------------------------------
    # Tree data
    # ------------------------------------------------------------------

    def set_item_data(
        self,
        tree_item,
        kind,
        item_id
    ):
        tree_item.setData(
            0,
            ROLE_KIND,
            kind
        )
        tree_item.setData(
            0,
            ROLE_ID,
            item_id
        )

    def item_data(
        self,
        tree_item,
        role
    ):
        if tree_item is None:
            return None

        value = tree_item.data(
            0,
            role
        )

        try:
            value = value.toString()
        except Exception:
            pass

        return text_type(
            value
        )

    def rebuild_cache(self):
        self.item_cache = {}

        for item in walk_items(
            self.working,
            include_folders=True
        ):
            self.item_cache[
                text_type(item["id"])
            ] = item

    def make_tree_item(self, data):
        return make_layout_tree_item(
            self,
            data,
            None
        )

    def populate_tree(self):
        self.current_item_id = None
        self.tree.clear()
        self.rebuild_cache()

        for section in self.working.get("sections", []) or []:
            self.tree.addTopLevelItem(
                self.make_tree_item(section)
            )

        if self.tree.topLevelItemCount():
            first = self.tree.topLevelItem(0)
            first.setExpanded(True)
            self.tree.setCurrentItem(first)
        else:
            self.show_empty_properties()

    def nearest_section(self, tree_item):
        current = tree_item
        while current is not None:
            if _is_section(self.item_data(current, ROLE_KIND)):
                return current
            current = current.parent()
        return None

    def ensure_root_section(self):
        for index in range(self.tree.topLevelItemCount()):
            current = self.tree.topLevelItem(index)
            if _is_section(self.item_data(current, ROLE_KIND)):
                return current

        kind = _default_section_kind()
        data = create_item(
            kind,
            {
                "name": "my_tools",
                "ui": {"label": "My Tools"},
            }
        )
        self.item_cache[data["id"]] = data

        tree_item = self.make_tree_item(data)
        self.tree.addTopLevelItem(tree_item)
        tree_item.setExpanded(True)
        return tree_item

    def fix_tree_structure(self):
        return fix_layout_tree_structure(self)

    def sync_working_from_tree(self):
        return sync_layout_working_from_tree(self)

    def tree_changed(self):
        self.sync_working_from_tree()
        self.status.setText(
            "Modified — Apply or Accept to save."
        )
        self.commit_history(
            sync_tree=False
        )

    # ------------------------------------------------------------------
    # History / clipboard
    # ------------------------------------------------------------------

    def schedule_history(self):
        if self._history_restoring:
            return
        self.history_timer.start()

    def commit_history(
        self,
        sync_tree=True
    ):
        if self._history_restoring:
            return

        if self.history_timer.isActive():
            self.history_timer.stop()

        if sync_tree:
            self.sync_working_from_tree()

        if self.working == self._history_current:
            return

        self.undo_stack.append(
            copy.deepcopy(self._history_current)
        )
        if len(self.undo_stack) > 100:
            self.undo_stack = self.undo_stack[-100:]

        self._history_current = copy.deepcopy(
            self.working
        )
        self.redo_stack = []

    def _restore_history(
        self,
        document,
        label
    ):
        current_id = self.current_item_id
        self._history_restoring = True
        try:
            self.working = copy.deepcopy(document)
            self.populate_tree()

            if current_id:
                tree_item = self.tree_item_by_id(
                    current_id
                )
                if tree_item is not None:
                    self.tree.setCurrentItem(
                        tree_item
                    )

            self._history_current = copy.deepcopy(
                self.working
            )
            self.status.setText(
                "{0} — Apply or Accept to save.".format(
                    label
                )
            )
        finally:
            self._history_restoring = False

    def undo(self):
        if self.history_timer.isActive():
            self.commit_history()

        if not self.undo_stack:
            return

        current = copy.deepcopy(
            self._history_current
        )
        previous = self.undo_stack.pop()
        self.redo_stack.append(current)
        self._restore_history(
            previous,
            "Undo"
        )

    def redo(self):
        if self.history_timer.isActive():
            self.commit_history()

        if not self.redo_stack:
            return

        current = copy.deepcopy(
            self._history_current
        )
        next_state = self.redo_stack.pop()
        self.undo_stack.append(current)
        self._restore_history(
            next_state,
            "Redo"
        )

    def _used_names(self):
        return set(
            text_type(item.get("name", ""))
            for item in walk_items(
                self.working,
                include_folders=True
            )
        )

    def _unique_name(
        self,
        base,
        used_names
    ):
        base = sanitize_name(
            base,
            "item"
        )

        if base not in used_names:
            used_names.add(base)
            return base

        index = 2
        while True:
            candidate = "{0}_{1}".format(
                base,
                index
            )
            if candidate not in used_names:
                used_names.add(candidate)
                return candidate
            index += 1

    def _clone_data(
        self,
        data,
        used_names=None
    ):
        if used_names is None:
            used_names = self._used_names()

        clone = copy.deepcopy(data)
        clone["id"] = new_id()
        clone["name"] = self._unique_name(
            clone.get(
                "name",
                clone.get("kind", "item")
            ),
            used_names
        )

        if _is_container(clone.get("kind")):
            clone["items"] = [
                self._clone_data(
                    child,
                    used_names
                )
                for child in clone.get("items", []) or []
            ]

        return clone

    def _cache_subtree(self, data):
        self.item_cache[
            text_type(data["id"])
        ] = data

        if _is_container(data.get("kind")):
            for child in data.get("items", []) or []:
                self._cache_subtree(child)

    def copy_selected(self):
        global _EDITOR_CLIPBOARD

        current = self.tree.currentItem()
        if current is None:
            return

        self.sync_working_from_tree()
        item_id = self.item_data(
            current,
            ROLE_ID
        )
        data = self.item_cache.get(item_id)

        if data is None:
            return

        self.clipboard_item = copy.deepcopy(data)
        _EDITOR_CLIPBOARD = copy.deepcopy(data)
        self.status.setText(
            "Copied: {0}".format(
                _item_label(data) or "Item"
            )
        )

    def _insert_cloned_tree_item(
        self,
        data,
        sibling=False
    ):
        return insert_layout_cloned_tree_item(
            self,
            data,
            sibling=sibling
        )

    def paste_selected(self):
        source = self.clipboard_item or _EDITOR_CLIPBOARD
        if source is None:
            return

        self.clipboard_item = copy.deepcopy(source)
        self.sync_working_from_tree()
        clone = self._clone_data(
            source,
            self._used_names()
        )
        tree_item = self._insert_cloned_tree_item(
            clone,
            sibling=False
        )
        self.tree.setCurrentItem(tree_item)
        self.fix_tree_structure()
        self.tree_changed()

    def duplicate_selected(
        self,
        target_item=None
    ):
        current = target_item or self.tree.currentItem()
        if current is None:
            return

        self.tree.setCurrentItem(
            current
        )
        self.sync_working_from_tree()
        item_id = self.item_data(current, ROLE_ID)
        data = self.item_cache.get(item_id)
        if data is None:
            return

        clone = self._clone_data(
            data,
            self._used_names()
        )
        tree_item = self._insert_cloned_tree_item(
            clone,
            sibling=True
        )

        try:
            tree_item.setExpanded(
                current.isExpanded()
            )
        except Exception:
            pass

        self.fix_tree_structure()
        self.tree_changed()

        selected = self.tree_item_by_id(
            text_type(clone["id"])
        )
        if selected is None:
            selected = tree_item

        self.tree.setCurrentItem(
            selected
        )
        try:
            self.tree.scrollToItem(
                selected,
                QtGui.QAbstractItemView.EnsureVisible
            )
        except Exception:
            pass

    def show_tree_context_menu(self, point):
        item = self.tree.itemAt(point)
        if item is not None:
            self.tree.setCurrentItem(item)

        menu = QtGui.QMenu(self.tree)
        undo_action = menu.addAction("Undo")
        redo_action = menu.addAction("Redo")
        undo_action.setEnabled(bool(self.undo_stack))
        redo_action.setEnabled(bool(self.redo_stack))
        menu.addSeparator()
        copy_action = menu.addAction("Copy")
        paste_action = menu.addAction("Paste")
        duplicate_action = menu.addAction("Duplicate")
        paste_action.setEnabled(self.clipboard_item is not None)
        menu.addSeparator()
        delete_action = menu.addAction("Delete")

        action = menu.exec_(
            self.tree.viewport().mapToGlobal(point)
        )

        if action == undo_action:
            self.undo()
        elif action == redo_action:
            self.redo()
        elif action == copy_action:
            self.copy_selected()
        elif action == paste_action:
            self.paste_selected()
        elif action == duplicate_action:
            self.duplicate_selected(
                item
            )
        elif action == delete_action:
            self.delete_selected()

    # ------------------------------------------------------------------
    # Create / move / delete
    # ------------------------------------------------------------------

    def palette_item_kind(
        self,
        palette_item
    ):
        if palette_item is None:
            return ""

        try:
            kind = palette_item.data(
                0,
                ROLE_KIND
            )
        except TypeError:
            kind = palette_item.data(
                ROLE_KIND
            )

        try:
            kind = kind.toString()
        except Exception:
            pass

        return text_type(
            kind or ""
        )

    def filter_palette(
        self,
        value
    ):
        query = text_type(
            value or ""
        ).strip().lower()

        for group_index in range(
            self.palette.topLevelItemCount()
        ):
            group = self.palette.topLevelItem(
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
                kind = self.palette_item_kind(
                    child
                ).lower()

                visible = (
                    not query or
                    query in label or
                    query in tooltip or
                    query in kind
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

    def filter_existing_parameters(
        self,
        value
    ):
        return filter_editor_structure(
            self,
            value
        )

    def create_from_palette(
        self,
        palette_item,
        column=0
    ):
        return create_layout_from_palette(
            self,
            palette_item,
            column=column
        )

    def move_selected(
        self,
        direction
    ):
        item = self.tree.currentItem()

        if item is None:
            return

        parent = item.parent()

        if parent is None:
            index = self.tree.indexOfTopLevelItem(
                item
            )
            new_index = index + direction

            if (
                new_index < 0 or
                new_index >= self.tree.topLevelItemCount()
            ):
                return

            item = self.tree.takeTopLevelItem(
                index
            )
            self.tree.insertTopLevelItem(
                new_index,
                item
            )
        else:
            index = parent.indexOfChild(
                item
            )
            new_index = index + direction

            if (
                new_index < 0 or
                new_index >= parent.childCount()
            ):
                return

            item = parent.takeChild(
                index
            )
            parent.insertChild(
                new_index,
                item
            )

        self.tree.setCurrentItem(
            item
        )
        self.tree_changed()

    def delete_selected(self):
        item = self.tree.currentItem()
        if item is None:
            return

        definition = _definition(
            self.item_data(item, ROLE_KIND)
        )
        if (
            definition is not None and
            definition.is_container and
            item.childCount()
        ):
            answer = QtGui.QMessageBox.question(
                self,
                "Delete {0}".format(definition.title),
                "Delete this {0} and everything inside it?".format(
                    definition.title
                ),
                QtGui.QMessageBox.Yes |
                QtGui.QMessageBox.No,
                QtGui.QMessageBox.No
            )
            if answer != QtGui.QMessageBox.Yes:
                return

        parent = item.parent()
        if parent is None:
            index = self.tree.indexOfTopLevelItem(item)
            self.tree.takeTopLevelItem(index)
        else:
            parent.removeChild(item)

        if not self.tree.topLevelItemCount():
            self.ensure_root_section()

        self.fix_tree_structure()
        self.tree_changed()

        if self.tree.topLevelItemCount():
            self.tree.setCurrentItem(
                self.tree.topLevelItem(0)
            )

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    def clear_property_editor(self):
        if self.current_property_editor is None:
            return

        self.property_layout.removeWidget(
            self.current_property_editor
        )
        self.current_property_editor.deleteLater()
        self.current_property_editor = None

    def show_empty_properties(self):
        self.clear_property_editor()

        editor = create_editor(
            "__empty__",
            toolbox=self.toolbox,
            parent=self.property_host
        )
        self.current_property_editor = editor
        self.property_layout.addWidget(
            editor
        )

    def selection_changed(
        self,
        current,
        previous
    ):
        if current is None:
            self.current_item_id = None
            self.show_empty_properties()
            return

        item_id = self.item_data(
            current,
            ROLE_ID
        )
        kind = self.item_data(
            current,
            ROLE_KIND
        )

        data = self.item_cache.get(
            item_id
        )

        if data is None:
            return

        self.clear_property_editor()

        editor = create_editor(
            kind,
            toolbox=self.toolbox,
            parent=self.property_host
        )
        try:
            parent_tree = current.parent()
            parent_data = None
            parent_kind = ""
            if parent_tree is not None:
                parent_kind = self.item_data(
                    parent_tree,
                    ROLE_KIND
                )
                parent_id = self.item_data(
                    parent_tree,
                    ROLE_ID
                )
                parent_data = self.item_cache.get(parent_id)
            editor.set_parent_layout_context(
                parent_kind,
                parent_data
            )
        except Exception:
            pass
        editor.bind(
            data
        )

        try:
            editor.changed.connect(
                self.property_changed
            )
        except Exception:
            pass

        self.current_property_editor = editor
        self.current_item_id = item_id

        self.property_layout.addWidget(
            editor
        )
        try:
            self.property_scroll.verticalScrollBar().setValue(
                0
            )
        except Exception:
            pass

    def property_changed(self):
        if not self.current_item_id:
            return

        tree_item = self.tree_item_by_id(
            self.current_item_id
        )
        data = self.item_cache.get(
            self.current_item_id
        )

        if (
            tree_item is None or
            data is None
        ):
            return

        tree_item.setText(
            0,
            _item_label(data)
        )
        tree_item.setText(
            1,
            text_type(data.get("name", ""))
        )
        definition = _definition(data.get("kind"))
        tree_item.setText(
            2,
            definition.title
            if definition is not None
            else text_type(data.get("kind", "")).title()
        )

        self.status.setText(
            "Modified — Apply or Accept to save."
        )
        self.schedule_history()

    def tree_item_by_id(
        self,
        item_id
    ):
        def recurse(tree_item):
            if self.item_data(
                tree_item,
                ROLE_ID
            ) == item_id:
                return tree_item

            for index in range(
                tree_item.childCount()
            ):
                found = recurse(
                    tree_item.child(index)
                )

                if found is not None:
                    return found

            return None

        for index in range(
            self.tree.topLevelItemCount()
        ):
            found = recurse(
                self.tree.topLevelItem(index)
            )

            if found is not None:
                return found

        return None

    # ------------------------------------------------------------------
    # Import / Export
    # ------------------------------------------------------------------

    def _dialog_path(
        self,
        result
    ):
        if isinstance(
            result,
            (tuple, list)
        ):
            if not result:
                return ""

            result = result[0]

        try:
            result = result.toString()
        except Exception:
            pass

        return text_type(
            result or ""
        )

    def export_settings(self):
        self.sync_working_from_tree()

        if not self.validate_internal_names():
            return

        default_path = os.path.join(
            os.path.dirname(config_path()),
            "{0}_script_toolbox_export.json".format(
                HOST.key
            )
        )

        result = QtGui.QFileDialog.getSaveFileName(
            self,
            "Export Toolbox Settings",
            default_path,
            "JSON Files (*.json);;All Files (*.*)"
        )

        path = self._dialog_path(result)

        if not path:
            return

        if not path.lower().endswith(".json"):
            path += ".json"

        try:
            export_config(
                self.working,
                path
            )
            self.status.setText(
                "Exported: {0}".format(
                    os.path.basename(path)
                )
            )
        except Exception as exc:
            QtGui.QMessageBox.critical(
                self,
                "Export Failed",
                text_type(exc)
            )

    def import_settings(self):
        result = QtGui.QFileDialog.getOpenFileName(
            self,
            "Import Toolbox Settings",
            os.path.dirname(config_path()),
            "JSON Files (*.json);;All Files (*.*)"
        )
        path = self._dialog_path(result)

        if not path:
            return

        modes = [
            "Replace Toolbox",
            "Append to Toolbox",
            "Insert into Selected Section",
        ]
        choice = QtGui.QInputDialog.getItem(
            self,
            "Import Toolbox Settings",
            "Import mode:",
            modes,
            0,
            False
        )

        if isinstance(choice, (tuple, list)):
            if len(choice) < 2 or not choice[1]:
                return
            mode = text_type(choice[0])
        else:
            mode = text_type(choice)

        if not mode:
            return

        try:
            imported = import_config(path)
            self.sync_working_from_tree()
            current_id = self.current_item_id

            if mode == "Replace Toolbox":
                self.working = normalize_document(
                    copy.deepcopy(imported)
                )

            elif mode == "Append to Toolbox":
                used_names = self._used_names()
                for section in imported.get("sections", []):
                    self.working.setdefault("sections", []).append(
                        self._clone_data(
                            section,
                            used_names
                        )
                    )

            else:
                current = self.tree.currentItem()
                target_tree = self.nearest_section(current)

                if target_tree is None:
                    target_tree = self.ensure_root_section()

                target_id = self.item_data(
                    target_tree,
                    ROLE_ID
                )
                target = self.item_cache.get(target_id)

                if target is None:
                    raise RuntimeError(
                        "Select a section before using Insert mode."
                    )

                used_names = self._used_names()
                target.setdefault("items", [])

                for section in imported.get("sections", []):
                    target["items"].append(
                        self._clone_data(
                            section,
                            used_names
                        )
                    )

                current_id = target_id

            self.populate_tree()
            if current_id:
                selected = self.tree_item_by_id(current_id)
                if selected is not None:
                    self.tree.setCurrentItem(selected)

            self.commit_history(sync_tree=False)
            self.status.setText(
                "Imported {0} ({1}). Apply or Accept to save.".format(
                    os.path.basename(path),
                    mode
                )
            )
        except Exception as exc:
            QtGui.QMessageBox.critical(
                self,
                "Import Failed",
                text_type(exc)
            )

    # ------------------------------------------------------------------
    # Validation / Apply
    # ------------------------------------------------------------------

    def validate_internal_names(self):
        names = {}

        for item in walk_items(
            self.working,
            include_folders=True
        ):
            name = text_type(item.get("name", ""))

            if name in names:
                QtGui.QMessageBox.warning(
                    self,
                    "Duplicate Name",
                    "Name '{0}' is used more than once.".format(
                        name
                    )
                )
                return False

            names[name] = item.get("id")

        return True

    def apply_changes(self):
        self.fix_tree_structure()
        self.sync_working_from_tree()

        if not self.validate_internal_names():
            return False

        self.toolbox.config = normalize_document(
            copy.deepcopy(
                self.working
            )
        )
        self.toolbox.save()
        self.toolbox.rebuild()

        self.working = copy.deepcopy(
            self.toolbox.config
        )
        self.populate_tree()
        self._history_current = copy.deepcopy(
            self.working
        )

        self.status.setText(
            "Applied."
        )
        return True

    def accept_changes(self):
        if self.apply_changes():
            self.accept()


__all__ = [
    "InterfaceEditor",
]
