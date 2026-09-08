# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore
from ..compat import QtGui
from ..constants import CONFIG_VERSION
from ..model import create_item
from ..model import is_container_kind
from ..model import is_layout_kind
from ..pycompat import text_type


_LAYOUT_ADAPTER_MARKER = "_script_toolbox_layout_editor_adapter"
_LAYOUT_LEGACY_BASE = "_script_toolbox_layout_legacy_base"
_DOCUMENT_ADAPTER_MARKER = "_script_toolbox_document_controller_adapter"
_DOCUMENT_LEGACY_BASE = "_script_toolbox_legacy_interface_editor"


def _unwrap_base(base_class):
    changed = True
    while changed:
        changed = False

        if getattr(
            base_class,
            _DOCUMENT_ADAPTER_MARKER,
            False
        ):
            legacy = getattr(
                base_class,
                _DOCUMENT_LEGACY_BASE,
                None
            )
            if legacy is not None and legacy is not base_class:
                base_class = legacy
                changed = True
                continue

        if getattr(
            base_class,
            _LAYOUT_ADAPTER_MARKER,
            False
        ):
            legacy = getattr(
                base_class,
                _LAYOUT_LEGACY_BASE,
                None
            )
            if legacy is not None and legacy is not base_class:
                base_class = legacy
                changed = True

    return base_class


def build_layout_editor_class(base_class):
    """Add composable Row / Column structure to the legacy Qt editor."""
    base_class = _unwrap_base(base_class)

    class InterfaceEditor(base_class):

        def make_tree_item(self, data):
            tree_item = base_class.make_tree_item(
                self,
                data
            )
            kind = text_type(
                data.get("kind", "")
            ).lower()

            if kind != "column":
                return tree_item

            flags = tree_item.flags()
            flags |= QtCore.Qt.ItemIsDropEnabled
            tree_item.setFlags(flags)

            for column in range(3):
                tree_item.setForeground(
                    column,
                    QtGui.QBrush(
                        QtGui.QColor("#c7b7d7")
                    )
                )

            for child in data.get("items", []) or []:
                tree_item.addChild(
                    self.make_tree_item(child)
                )

            tree_item.setExpanded(True)
            return tree_item

        def fix_tree_structure(self):
            # The root remains Folder-only. Rows and Columns are composable
            # below a Folder, while nested Folders are kept out of layouts.
            index = 0

            while index < self.tree.topLevelItemCount():
                item = self.tree.topLevelItem(index)
                if self.item_data(
                    item,
                    self.ROLE_KIND if hasattr(self, "ROLE_KIND") else QtCore.Qt.UserRole
                ) == "folder":
                    index += 1
                    continue

                orphan = self.tree.takeTopLevelItem(index)
                target = self.ensure_root_folder()
                if target is orphan:
                    self.tree.insertTopLevelItem(index, orphan)
                    index += 1
                    continue

                target.addChild(orphan)
                target.setExpanded(True)

            # ROLE_KIND is a module constant on the legacy implementation, not
            # a class attribute. Resolve through the stable user-role value.
            role_kind = QtCore.Qt.UserRole

            def kind_of(tree_item):
                return self.item_data(
                    tree_item,
                    role_kind
                )

            def normalize_container(container, nearest_folder):
                container_kind = kind_of(container)
                child_index = 0

                while child_index < container.childCount():
                    child = container.child(child_index)
                    child_kind = kind_of(child)

                    if container_kind in ("row", "column") and child_kind == "folder":
                        moved = container.takeChild(child_index)
                        nearest_folder.addChild(moved)
                        nearest_folder.setExpanded(True)
                        normalize_container(moved, moved)
                        continue

                    if child_kind == "folder":
                        normalize_container(child, child)
                        child_index += 1
                        continue

                    if child_kind in ("row", "column"):
                        normalize_container(
                            child,
                            nearest_folder
                        )
                        child_index += 1
                        continue

                    # Leaf controls cannot own children. Preserve accidental
                    # drag/drop descendants by moving them beside the control.
                    while child.childCount():
                        nested = child.takeChild(0)
                        container.insertChild(
                            child_index + 1,
                            nested
                        )
                        child_index += 1

                    child_index += 1

            for root_index in range(
                self.tree.topLevelItemCount()
            ):
                root = self.tree.topLevelItem(root_index)
                normalize_container(root, root)

        def sync_working_from_tree(self):
            if self.current_property_editor is not None:
                try:
                    self.current_property_editor.write_to_item()
                except Exception:
                    pass

            role_kind = QtCore.Qt.UserRole
            role_id = QtCore.Qt.UserRole + 1

            def data_from_tree(tree_item):
                item_id = self.item_data(
                    tree_item,
                    role_id
                )
                kind = self.item_data(
                    tree_item,
                    role_kind
                )

                data = self.item_cache.get(item_id)
                if data is None:
                    data = create_item(
                        kind,
                        {
                            "id": item_id,
                            "name": text_type(
                                tree_item.text(1)
                            ),
                            "label": text_type(
                                tree_item.text(0)
                            ),
                        }
                    )

                data["kind"] = kind
                data["label"] = text_type(
                    tree_item.text(0)
                )
                data["name"] = text_type(
                    tree_item.text(1)
                )

                if is_container_kind(kind):
                    children = []
                    for child_index in range(
                        tree_item.childCount()
                    ):
                        child = tree_item.child(child_index)
                        child_kind = self.item_data(
                            child,
                            role_kind
                        )
                        if is_layout_kind(kind) and child_kind == "folder":
                            continue
                        children.append(
                            data_from_tree(child)
                        )
                    data["items"] = children

                return data

            sections = []
            for index in range(
                self.tree.topLevelItemCount()
            ):
                root_item = self.tree.topLevelItem(index)
                if self.item_data(
                    root_item,
                    role_kind
                ) != "folder":
                    continue
                sections.append(
                    data_from_tree(root_item)
                )

            self.working = {
                "version": CONFIG_VERSION,
                "sections": sections,
            }
            self.rebuild_cache()

        def _insert_cloned_tree_item(
            self,
            data,
            sibling=False
        ):
            tree_item = self.make_tree_item(data)
            self._cache_subtree(data)
            current = self.tree.currentItem()
            kind = text_type(
                data.get("kind", "")
            ).lower()

            if current is None:
                if kind == "folder":
                    self.tree.addTopLevelItem(tree_item)
                else:
                    root = self.ensure_root_folder()
                    root.addChild(tree_item)
                    root.setExpanded(True)
                return tree_item

            role_kind = QtCore.Qt.UserRole
            current_kind = self.item_data(
                current,
                role_kind
            )
            parent = current.parent()

            if sibling:
                if parent is None:
                    if kind == "folder":
                        index = self.tree.indexOfTopLevelItem(current)
                        self.tree.insertTopLevelItem(
                            index + 1,
                            tree_item
                        )
                    else:
                        current.addChild(tree_item)
                        current.setExpanded(True)
                else:
                    if (
                        is_layout_kind(
                            self.item_data(parent, role_kind)
                        ) and
                        kind == "folder"
                    ):
                        folder = self.nearest_folder(parent)
                        folder.addChild(tree_item)
                        folder.setExpanded(True)
                    else:
                        index = parent.indexOfChild(current)
                        parent.insertChild(
                            index + 1,
                            tree_item
                        )
                return tree_item

            if is_container_kind(current_kind):
                if is_layout_kind(current_kind) and kind == "folder":
                    folder = self.nearest_folder(current)
                    folder.addChild(tree_item)
                    folder.setExpanded(True)
                else:
                    current.addChild(tree_item)
                    current.setExpanded(True)
                return tree_item

            if parent is not None:
                parent_kind = self.item_data(
                    parent,
                    role_kind
                )
                if is_layout_kind(parent_kind) and kind == "folder":
                    folder = self.nearest_folder(parent)
                    folder.addChild(tree_item)
                    folder.setExpanded(True)
                    return tree_item

                index = parent.indexOfChild(current)
                parent.insertChild(
                    index + 1,
                    tree_item
                )
                return tree_item

            if kind == "folder":
                self.tree.addTopLevelItem(tree_item)
            else:
                root = self.ensure_root_folder()
                root.addChild(tree_item)
                root.setExpanded(True)

            return tree_item

        def create_from_palette(
            self,
            palette_item,
            column=0
        ):
            kind = self.palette_item_kind(palette_item)
            if not kind:
                return

            data = create_item(kind)
            self.item_cache[data["id"]] = data
            tree_item = self.make_tree_item(data)

            current = self.tree.currentItem()
            parent = None
            role_kind = QtCore.Qt.UserRole

            if current is not None:
                current_kind = self.item_data(
                    current,
                    role_kind
                )

                if kind == "folder":
                    if current_kind == "folder":
                        parent = current
                    else:
                        parent = self.nearest_folder(current)
                elif is_container_kind(current_kind):
                    parent = current
                else:
                    current_parent = current.parent()
                    if (
                        current_parent is not None and
                        is_container_kind(
                            self.item_data(
                                current_parent,
                                role_kind
                            )
                        )
                    ):
                        parent = current_parent
                    else:
                        parent = self.nearest_folder(current)

            if kind != "folder" and parent is None:
                parent = self.ensure_root_folder()

            if parent is None:
                self.tree.addTopLevelItem(tree_item)
            else:
                if (
                    is_layout_kind(
                        self.item_data(parent, role_kind)
                    ) and
                    kind == "folder"
                ):
                    parent = self.nearest_folder(parent)

                parent.addChild(tree_item)
                parent.setExpanded(True)

            self.tree.setCurrentItem(tree_item)
            self.fix_tree_structure()
            self.tree_changed()

        def delete_selected(self):
            item = self.tree.currentItem()
            if item is None:
                return

            kind = self.item_data(
                item,
                QtCore.Qt.UserRole
            )

            if (
                kind in ("row", "column") and
                item.childCount()
            ):
                answer = QtGui.QMessageBox.question(
                    self,
                    "Delete {0}".format(kind.title()),
                    "Delete this {0} and everything inside it?".format(
                        kind.title()
                    ),
                    QtGui.QMessageBox.Yes |
                    QtGui.QMessageBox.No,
                    QtGui.QMessageBox.No
                )
                if answer != QtGui.QMessageBox.Yes:
                    return

            return base_class.delete_selected(self)

    setattr(
        InterfaceEditor,
        _LAYOUT_ADAPTER_MARKER,
        True
    )
    setattr(
        InterfaceEditor,
        _LAYOUT_LEGACY_BASE,
        base_class
    )
    InterfaceEditor.__name__ = "InterfaceEditor"
    return InterfaceEditor


__all__ = [
    "build_layout_editor_class",
]
