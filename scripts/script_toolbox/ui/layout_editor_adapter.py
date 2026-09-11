# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore
from ..compat import QtGui
from ..constants import CONFIG_VERSION
from ..model import create_item
from ..model import is_container_kind
from ..model import is_layout_kind
from ..pycompat import text_type
from ..style.palette import TEXT_STRUCTURE_COLUMN


def make_layout_tree_item(
    editor,
    data,
    base_make_tree_item
):
    """Create a tree item and add Column-specific container behavior."""
    tree_item = base_make_tree_item(
        editor,
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
                QtGui.QColor(TEXT_STRUCTURE_COLUMN)
            )
        )

    for child in data.get("items", []) or []:
        tree_item.addChild(
            editor.make_tree_item(child)
        )

    tree_item.setExpanded(True)
    return tree_item


def fix_layout_tree_structure(editor):
    """Normalize Folder / Row / Column nesting after drag and drop."""
    index = 0

    while index < editor.tree.topLevelItemCount():
        item = editor.tree.topLevelItem(index)
        if editor.item_data(
            item,
            QtCore.Qt.UserRole
        ) == "folder":
            index += 1
            continue

        orphan = editor.tree.takeTopLevelItem(index)
        target = editor.ensure_root_folder()
        if target is orphan:
            editor.tree.insertTopLevelItem(index, orphan)
            index += 1
            continue

        target.addChild(orphan)
        target.setExpanded(True)

    role_kind = QtCore.Qt.UserRole

    def kind_of(tree_item):
        return editor.item_data(
            tree_item,
            role_kind
        )

    def normalize_container(container, nearest_folder):
        container_kind = kind_of(container)
        child_index = 0

        while child_index < container.childCount():
            child = container.child(child_index)
            child_kind = kind_of(child)

            if (
                container_kind in ("row", "column") and
                child_kind == "folder"
            ):
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

            while child.childCount():
                nested = child.takeChild(0)
                container.insertChild(
                    child_index + 1,
                    nested
                )
                child_index += 1

            child_index += 1

    for root_index in range(
        editor.tree.topLevelItemCount()
    ):
        root = editor.tree.topLevelItem(root_index)
        normalize_container(root, root)


def sync_layout_working_from_tree(editor):
    """Serialize the current Folder / Row / Column tree into editor.working."""
    if editor.current_property_editor is not None:
        try:
            editor.current_property_editor.write_to_item()
        except Exception:
            pass

    role_kind = QtCore.Qt.UserRole
    role_id = QtCore.Qt.UserRole + 1

    def data_from_tree(tree_item):
        item_id = editor.item_data(
            tree_item,
            role_id
        )
        kind = editor.item_data(
            tree_item,
            role_kind
        )

        data = editor.item_cache.get(item_id)
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
                child_kind = editor.item_data(
                    child,
                    role_kind
                )
                if (
                    is_layout_kind(kind) and
                    child_kind == "folder"
                ):
                    continue
                children.append(
                    data_from_tree(child)
                )
            data["items"] = children

        return data

    sections = []
    for index in range(
        editor.tree.topLevelItemCount()
    ):
        root_item = editor.tree.topLevelItem(index)
        if editor.item_data(
            root_item,
            role_kind
        ) != "folder":
            continue
        sections.append(
            data_from_tree(root_item)
        )

    editor.working = {
        "version": CONFIG_VERSION,
        "sections": sections,
    }
    editor.rebuild_cache()


def insert_layout_cloned_tree_item(
    editor,
    data,
    sibling=False
):
    """Insert a cloned subtree while respecting layout Folder restrictions."""
    tree_item = editor.make_tree_item(data)
    editor._cache_subtree(data)
    current = editor.tree.currentItem()
    kind = text_type(
        data.get("kind", "")
    ).lower()

    if current is None:
        if kind == "folder":
            editor.tree.addTopLevelItem(tree_item)
        else:
            root = editor.ensure_root_folder()
            root.addChild(tree_item)
            root.setExpanded(True)
        return tree_item

    role_kind = QtCore.Qt.UserRole
    current_kind = editor.item_data(
        current,
        role_kind
    )
    parent = current.parent()

    if sibling:
        if parent is None:
            if kind == "folder":
                index = editor.tree.indexOfTopLevelItem(current)
                editor.tree.insertTopLevelItem(
                    index + 1,
                    tree_item
                )
            else:
                current.addChild(tree_item)
                current.setExpanded(True)
        else:
            if (
                is_layout_kind(
                    editor.item_data(parent, role_kind)
                ) and
                kind == "folder"
            ):
                folder = editor.nearest_folder(parent)
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
            folder = editor.nearest_folder(current)
            folder.addChild(tree_item)
            folder.setExpanded(True)
        else:
            current.addChild(tree_item)
            current.setExpanded(True)
        return tree_item

    if parent is not None:
        parent_kind = editor.item_data(
            parent,
            role_kind
        )
        if is_layout_kind(parent_kind) and kind == "folder":
            folder = editor.nearest_folder(parent)
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
        editor.tree.addTopLevelItem(tree_item)
    else:
        root = editor.ensure_root_folder()
        root.addChild(tree_item)
        root.setExpanded(True)

    return tree_item


def create_layout_from_palette(
    editor,
    palette_item,
    column=0
):
    """Create an item from the palette using Row / Column nesting rules."""
    kind = editor.palette_item_kind(palette_item)
    if not kind:
        return

    data = create_item(kind)
    editor.item_cache[data["id"]] = data
    tree_item = editor.make_tree_item(data)

    current = editor.tree.currentItem()
    parent = None
    role_kind = QtCore.Qt.UserRole

    if current is not None:
        current_kind = editor.item_data(
            current,
            role_kind
        )

        if kind == "folder":
            if current_kind == "folder":
                parent = current
            else:
                parent = editor.nearest_folder(current)
        elif is_container_kind(current_kind):
            parent = current
        else:
            current_parent = current.parent()
            if (
                current_parent is not None and
                is_container_kind(
                    editor.item_data(
                        current_parent,
                        role_kind
                    )
                )
            ):
                parent = current_parent
            else:
                parent = editor.nearest_folder(current)

    if kind != "folder" and parent is None:
        parent = editor.ensure_root_folder()

    if parent is None:
        editor.tree.addTopLevelItem(tree_item)
    else:
        if (
            is_layout_kind(
                editor.item_data(parent, role_kind)
            ) and
            kind == "folder"
        ):
            parent = editor.nearest_folder(parent)

        parent.addChild(tree_item)
        parent.setExpanded(True)

    editor.tree.setCurrentItem(tree_item)
    editor.fix_tree_structure()
    editor.tree_changed()


def delete_layout_selected(
    editor,
    base_delete_selected
):
    """Confirm destructive Row / Column deletion, then remove the item."""
    item = editor.tree.currentItem()
    if item is None:
        return

    kind = editor.item_data(
        item,
        QtCore.Qt.UserRole
    )

    if (
        kind in ("row", "column") and
        item.childCount()
    ):
        answer = QtGui.QMessageBox.question(
            editor,
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

    return base_delete_selected(editor)


__all__ = [
    "create_layout_from_palette",
    "delete_layout_selected",
    "fix_layout_tree_structure",
    "insert_layout_cloned_tree_item",
    "make_layout_tree_item",
    "sync_layout_working_from_tree",
]
