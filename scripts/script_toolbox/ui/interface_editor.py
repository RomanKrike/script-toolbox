# -*- coding: utf-8 -*-
from __future__ import print_function

import copy
import os

from ..compat import QtCore
from ..compat import QtGui
from ..constants import CONFIG_VERSION
from ..constants import EDITOR_OBJECT_NAME
from ..core.config import config_path
from ..core.config import export_config
from ..core.config import import_config
from ..model import create_item
from ..model import normalize_document
from ..model import walk_items
from ..pycompat import text_type
from ..style import STYLE
from ..style import toolbar_icon
from .interface_tree import ExistingInterfaceTree
from .properties import create_editor


ROLE_KIND = QtCore.Qt.UserRole
ROLE_ID = QtCore.Qt.UserRole + 1


class InterfaceEditor(QtGui.QDialog):

    PALETTE_ITEMS = (
        ("Folder", "folder"),
        ("Row", "row"),
        ("Field", "field"),
        ("String", "string"),
        ("Integer", "integer"),
        ("Float", "float"),
        ("Checkbox", "checkbox"),
        ("Menu", "menu"),
        ("Color", "color"),
        ("Button", "button"),
        ("Label", "label"),
        ("Separator", "separator"),
    )

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

        self.setObjectName(
            EDITOR_OBJECT_NAME
        )
        self.setWindowTitle(
            "Edit Parameter Interface"
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
        root.setContentsMargins(
            8,
            8,
            8,
            8
        )
        root.setSpacing(
            7
        )

        heading = QtGui.QLabel(
            "Edit Parameter Interface  —  Script Toolbox"
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
            2
        )
        splitter.setChildrenCollapsible(
            False
        )
        root.addWidget(
            splitter,
            1
        )

        # Create Parameters -------------------------------------------------
        left = QtGui.QWidget()
        left.setObjectName(
            "EditorPane"
        )
        left_layout = QtGui.QVBoxLayout(
            left
        )
        left_layout.setContentsMargins(
            8,
            8,
            8,
            8
        )
        left_layout.setSpacing(
            6
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

        self.palette = QtGui.QListWidget()
        self.palette.setAlternatingRowColors(
            True
        )
        self.palette.setSpacing(
            1
        )

        for label, kind in self.PALETTE_ITEMS:
            item = QtGui.QListWidgetItem(
                label
            )
            item.setData(
                ROLE_KIND,
                kind
            )

            if kind in (
                "folder",
                "row"
            ):
                font = item.font()
                font.setBold(
                    True
                )
                item.setFont(
                    font
                )

            self.palette.addItem(
                item
            )

        self.palette.itemDoubleClicked.connect(
            self.create_from_palette
        )

        left_layout.addWidget(
            self.palette,
            1
        )

        hint = QtGui.QLabel(
            "Double-click to create. Drag items to reorder or nest.\n"
            "Row = horizontal layout. Folder = nested parameter group."
        )
        hint.setObjectName(
            "HintText"
        )
        hint.setWordWrap(
            True
        )
        left_layout.addWidget(
            hint
        )

        splitter.addWidget(
            left
        )

        # Existing Parameters ----------------------------------------------
        center = QtGui.QWidget()
        center.setObjectName(
            "EditorPane"
        )
        center_layout = QtGui.QVBoxLayout(
            center
        )
        center_layout.setContentsMargins(
            8,
            8,
            8,
            8
        )
        center_layout.setSpacing(
            6
        )

        toolbar = QtGui.QHBoxLayout()
        toolbar.setSpacing(
            2
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

        for icon_name, tooltip, callback in (
            ("up", "Move Up", lambda: self.move_selected(-1)),
            ("down", "Move Down", lambda: self.move_selected(1)),
            ("delete", "Delete", self.delete_selected),
        ):
            button = QtGui.QToolButton()
            button.setObjectName(
                "IconButton"
            )
            button.setIcon(
                toolbar_icon(
                    icon_name
                )
            )
            button.setIconSize(
                QtCore.QSize(
                    16,
                    16
                )
            )
            button.setFixedSize(
                25,
                25
            )
            button.setToolTip(
                tooltip
            )
            button.clicked.connect(
                callback
            )
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
            18
        )
        self.tree.currentItemChanged.connect(
            self.selection_changed
        )

        center_layout.addWidget(
            self.tree,
            1
        )

        splitter.addWidget(
            center
        )

        # Parameter Description --------------------------------------------
        right = QtGui.QWidget()
        right.setObjectName(
            "EditorPane"
        )
        right_layout = QtGui.QVBoxLayout(
            right
        )
        right_layout.setContentsMargins(
            8,
            8,
            8,
            8
        )
        right_layout.setSpacing(
            6
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

        self.property_host = QtGui.QWidget()
        self.property_layout = QtGui.QVBoxLayout(
            self.property_host
        )
        self.property_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )
        right_layout.addWidget(
            self.property_host,
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

        # Bottom -----------------------------------------------------------
        bottom = QtGui.QHBoxLayout()
        bottom.setSpacing(
            6
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
            4
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
            78
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
            78
        )
        accept_button.clicked.connect(
            self.accept_changes
        )

        cancel_button = QtGui.QPushButton(
            "Cancel"
        )
        cancel_button.setMinimumWidth(
            78
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
        button = QtGui.QToolButton()
        button.setObjectName(
            "IconButton"
        )
        button.setIcon(
            toolbar_icon(
                icon_name
            )
        )
        button.setIconSize(
            QtCore.QSize(
                16,
                16
            )
        )
        button.setFixedSize(
            25,
            25
        )
        button.setToolTip(
            tooltip
        )
        button.clicked.connect(
            callback
        )
        return button

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
                text_type(
                    item["id"]
                )
            ] = item

    def make_tree_item(
        self,
        data
    ):
        kind = data.get(
            "kind",
            "button"
        )

        tree_item = QtGui.QTreeWidgetItem([
            data.get(
                "label",
                data.get(
                    "name",
                    ""
                )
            ),
            data.get(
                "name",
                ""
            ),
            kind.title()
        ])

        self.set_item_data(
            tree_item,
            kind,
            data["id"]
        )

        flags = tree_item.flags()
        flags |= QtCore.Qt.ItemIsDragEnabled

        if kind in (
            "folder",
            "row"
        ):
            flags |= QtCore.Qt.ItemIsDropEnabled
        else:
            flags &= ~QtCore.Qt.ItemIsDropEnabled

        tree_item.setFlags(
            flags
        )

        if kind in (
            "folder",
            "row"
        ):
            for child in data.get(
                "items",
                []
            ):
                tree_item.addChild(
                    self.make_tree_item(
                        child
                    )
                )

            tree_item.setExpanded(
                True
            )

        return tree_item

    def populate_tree(self):
        self.current_item_id = None
        self.tree.clear()
        self.rebuild_cache()

        for folder in self.working.get(
            "sections",
            []
        ):
            self.tree.addTopLevelItem(
                self.make_tree_item(
                    folder
                )
            )

        if self.tree.topLevelItemCount():
            first = self.tree.topLevelItem(
                0
            )
            first.setExpanded(
                True
            )
            self.tree.setCurrentItem(
                first
            )
        else:
            self.show_empty_properties()

    def nearest_folder(
        self,
        tree_item
    ):
        current = tree_item

        while current is not None:
            if self.item_data(
                current,
                ROLE_KIND
            ) == "folder":
                return current

            current = current.parent()

        return None

    def ensure_root_folder(self):
        if self.tree.topLevelItemCount():
            return self.tree.topLevelItem(
                0
            )

        data = create_item(
            "folder",
            {
                "name": "my_tools",
                "label": "My Tools",
            }
        )
        self.item_cache[
            data["id"]
        ] = data

        tree_item = self.make_tree_item(
            data
        )
        self.tree.addTopLevelItem(
            tree_item
        )
        tree_item.setExpanded(
            True
        )

        return tree_item

    def fix_tree_structure(self):
        # Root contains Folders only.
        index = 0

        while index < self.tree.topLevelItemCount():
            item = self.tree.topLevelItem(
                index
            )

            if self.item_data(
                item,
                ROLE_KIND
            ) == "folder":
                index += 1
                continue

            orphan = self.tree.takeTopLevelItem(
                index
            )
            target = self.ensure_root_folder()

            if target is orphan:
                target = None

            if target is None:
                self.tree.insertTopLevelItem(
                    index,
                    orphan
                )
                index += 1
                continue

            target.addChild(
                orphan
            )
            target.setExpanded(
                True
            )

        def normalize_folder(folder_item):
            child_index = 0

            while child_index < folder_item.childCount():
                child = folder_item.child(
                    child_index
                )
                kind = self.item_data(
                    child,
                    ROLE_KIND
                )

                if kind == "folder":
                    normalize_folder(
                        child
                    )
                    child.setExpanded(
                        True
                    )
                    child_index += 1
                    continue

                if kind == "row":
                    row_index = 0

                    while row_index < child.childCount():
                        nested = child.child(
                            row_index
                        )
                        nested_kind = self.item_data(
                            nested,
                            ROLE_KIND
                        )

                        if nested_kind in (
                            "folder",
                            "row"
                        ):
                            nested = child.takeChild(
                                row_index
                            )
                            folder_item.insertChild(
                                child_index + 1,
                                nested
                            )
                            child_index += 1
                            continue

                        row_index += 1

                    child.setExpanded(
                        True
                    )
                    child_index += 1
                    continue

                while child.childCount():
                    nested = child.takeChild(
                        0
                    )
                    folder_item.insertChild(
                        child_index + 1,
                        nested
                    )
                    child_index += 1

                child_index += 1

        for root_index in range(
            self.tree.topLevelItemCount()
        ):
            normalize_folder(
                self.tree.topLevelItem(
                    root_index
                )
            )

    def sync_working_from_tree(self):
        if self.current_property_editor is not None:
            try:
                self.current_property_editor.write_to_item()
            except Exception:
                pass

        def data_from_tree(tree_item):
            item_id = self.item_data(
                tree_item,
                ROLE_ID
            )
            kind = self.item_data(
                tree_item,
                ROLE_KIND
            )

            data = self.item_cache.get(
                item_id
            )

            if data is None:
                data = create_item(
                    kind,
                    {
                        "id": item_id,
                        "name": text_type(
                            tree_item.text(
                                1
                            )
                        ),
                        "label": text_type(
                            tree_item.text(
                                0
                            )
                        ),
                    }
                )

            data["kind"] = kind
            data["label"] = text_type(
                tree_item.text(
                    0
                )
            )
            data["name"] = text_type(
                tree_item.text(
                    1
                )
            )

            if kind in (
                "folder",
                "row"
            ):
                children = []

                for child_index in range(
                    tree_item.childCount()
                ):
                    child = tree_item.child(
                        child_index
                    )

                    if (
                        kind == "row" and
                        self.item_data(
                            child,
                            ROLE_KIND
                        ) in (
                            "folder",
                            "row"
                        )
                    ):
                        continue

                    children.append(
                        data_from_tree(
                            child
                        )
                    )

                data["items"] = children

            return data

        sections = []

        for index in range(
            self.tree.topLevelItemCount()
        ):
            root_item = self.tree.topLevelItem(
                index
            )

            if self.item_data(
                root_item,
                ROLE_KIND
            ) != "folder":
                continue

            sections.append(
                data_from_tree(
                    root_item
                )
            )

        self.working = {
            "version": CONFIG_VERSION,
            "sections": sections,
        }
        self.rebuild_cache()

    def tree_changed(self):
        self.sync_working_from_tree()
        self.status.setText(
            "Modified — Apply or Accept to save."
        )

    # ------------------------------------------------------------------
    # Create / move / delete
    # ------------------------------------------------------------------

    def create_from_palette(
        self,
        palette_item
    ):
        kind = palette_item.data(
            ROLE_KIND
        )

        try:
            kind = kind.toString()
        except Exception:
            pass

        kind = text_type(
            kind
        )

        data = create_item(
            kind
        )
        self.item_cache[
            data["id"]
        ] = data

        tree_item = self.make_tree_item(
            data
        )

        current = self.tree.currentItem()
        parent = None

        if current is not None:
            current_kind = self.item_data(
                current,
                ROLE_KIND
            )

            if kind == "folder":
                if current_kind == "folder":
                    parent = current
                else:
                    parent = self.nearest_folder(
                        current
                    )

            elif kind == "row":
                if current_kind == "folder":
                    parent = current
                else:
                    parent = self.nearest_folder(
                        current
                    )

            else:
                if current_kind in (
                    "folder",
                    "row"
                ):
                    parent = current
                else:
                    parent = self.nearest_folder(
                        current
                    )

        if (
            kind != "folder" and
            parent is None
        ):
            parent = self.ensure_root_folder()

        if parent is None:
            self.tree.addTopLevelItem(
                tree_item
            )
        else:
            parent.addChild(
                tree_item
            )
            parent.setExpanded(
                True
            )

        self.tree.setCurrentItem(
            tree_item
        )
        self.fix_tree_structure()
        self.tree_changed()

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

        kind = self.item_data(
            item,
            ROLE_KIND
        )

        if (
            kind == "folder" and
            item.childCount()
        ):
            answer = QtGui.QMessageBox.question(
                self,
                "Delete Folder",
                "Delete this Folder and everything inside it?",
                QtGui.QMessageBox.Yes |
                QtGui.QMessageBox.No,
                QtGui.QMessageBox.No
            )

            if answer != QtGui.QMessageBox.Yes:
                return

        parent = item.parent()

        if parent is None:
            index = self.tree.indexOfTopLevelItem(
                item
            )
            self.tree.takeTopLevelItem(
                index
            )
        else:
            parent.removeChild(
                item
            )

        if not self.tree.topLevelItemCount():
            self.ensure_root_folder()

        self.fix_tree_structure()
        self.tree_changed()

        if self.tree.topLevelItemCount():
            self.tree.setCurrentItem(
                self.tree.topLevelItem(
                    0
                )
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
            data.get(
                "label",
                data.get(
                    "name",
                    ""
                )
            )
        )
        tree_item.setText(
            1,
            data.get(
                "name",
                ""
            )
        )
        tree_item.setText(
            2,
            data.get(
                "kind",
                ""
            ).title()
        )

        self.status.setText(
            "Modified — Apply or Accept to save."
        )

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
                    tree_item.child(
                        index
                    )
                )

                if found is not None:
                    return found

            return None

        for index in range(
            self.tree.topLevelItemCount()
        ):
            found = recurse(
                self.tree.topLevelItem(
                    index
                )
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

            result = result[
                0
            ]

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
            os.path.dirname(
                config_path()
            ),
            "maya_script_toolbox_export.json"
        )

        result = QtGui.QFileDialog.getSaveFileName(
            self,
            "Export Toolbox Settings",
            default_path,
            "JSON Files (*.json);;All Files (*.*)"
        )

        path = self._dialog_path(
            result
        )

        if not path:
            return

        if not path.lower().endswith(
            ".json"
        ):
            path += ".json"

        try:
            export_config(
                self.working,
                path
            )
            self.status.setText(
                "Exported: {0}".format(
                    os.path.basename(
                        path
                    )
                )
            )
        except Exception as exc:
            QtGui.QMessageBox.critical(
                self,
                "Export Failed",
                text_type(
                    exc
                )
            )

    def import_settings(self):
        result = QtGui.QFileDialog.getOpenFileName(
            self,
            "Import Toolbox Settings",
            os.path.dirname(
                config_path()
            ),
            "JSON Files (*.json);;All Files (*.*)"
        )

        path = self._dialog_path(
            result
        )

        if not path:
            return

        try:
            self.working = import_config(
                path
            )
            self.populate_tree()
            self.status.setText(
                "Imported {0}. Apply or Accept to save.".format(
                    os.path.basename(
                        path
                    )
                )
            )
        except Exception as exc:
            QtGui.QMessageBox.critical(
                self,
                "Import Failed",
                text_type(
                    exc
                )
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
            name = text_type(
                item.get(
                    "name",
                    ""
                )
            )

            if name in names:
                QtGui.QMessageBox.warning(
                    self,
                    "Duplicate Name",
                    "Name '{0}' is used more than once.".format(
                        name
                    )
                )
                return False

            names[
                name
            ] = item.get(
                "id"
            )

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
