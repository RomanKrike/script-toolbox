# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore
from ..compat import QtGui
from ..constants import CONFIG_VERSION
from ..model import create_item
from ..model.item_builtins import register_builtin_items
from ..model.item_registry import ITEM_TYPES
from ..pycompat import text_type
from ..style.palette import STRUCTURE_FOLDER_BG
from ..style.palette import TEXT_STRUCTURE_COLUMN
from ..style.palette import TEXT_STRUCTURE_ROW


def _definition(kind):
    register_builtin_items()
    return ITEM_TYPES.get(text_type(kind or "").lower())


def _is_section(kind):
    definition = _definition(kind)
    return bool(definition and definition.has_capability("section"))


def _is_container(kind):
    definition = _definition(kind)
    return bool(definition and definition.is_container)


def _is_layout(kind):
    definition = _definition(kind)
    return bool(definition and definition.is_layout)


def _can_contain(parent_kind, child_kind):
    parent = _definition(parent_kind)
    child = _definition(child_kind)
    if parent is None or child is None or not parent.is_container:
        return False
    if parent.is_layout and child.has_capability("section"):
        return False
    return True


def _default_section_kind():
    register_builtin_items()
    for definition in ITEM_TYPES.creatable():
        if definition.has_capability("section"):
            return definition.kind
    raise RuntimeError("No creatable section Item type is registered.")


def _nearest_section(editor, tree_item):
    current = tree_item
    role_kind = QtCore.Qt.UserRole
    while current is not None:
        if _is_section(editor.item_data(current, role_kind)):
            return current
        current = current.parent()
    return None


def _ensure_root_section(editor):
    if editor.tree.topLevelItemCount():
        for index in range(editor.tree.topLevelItemCount()):
            candidate = editor.tree.topLevelItem(index)
            if _is_section(editor.item_data(candidate, QtCore.Qt.UserRole)):
                return candidate

    kind = _default_section_kind()
    data = create_item(
        kind,
        {
            "name": "my_tools",
            "ui": {"label": "My Tools"},
        }
    )
    editor.item_cache[data["id"]] = data
    tree_item = editor.make_tree_item(data)
    editor.tree.addTopLevelItem(tree_item)
    tree_item.setExpanded(True)
    return tree_item


def _tree_label(data):
    ui = data.get("ui", {}) or {}
    return text_type(ui.get("label", data.get("name", "")))


def _style_tree_item(tree_item, definition):
    if definition is None:
        return

    if definition.has_capability("section"):
        for column in range(3):
            font = tree_item.font(column)
            font.setBold(True)
            tree_item.setFont(column, font)
            tree_item.setBackground(
                column,
                QtGui.QBrush(QtGui.QColor(STRUCTURE_FOLDER_BG))
            )
        return

    if definition.is_layout:
        color = (
            TEXT_STRUCTURE_ROW
            if definition.layout_axis == "horizontal"
            else TEXT_STRUCTURE_COLUMN
        )
        for column in range(3):
            tree_item.setForeground(
                column,
                QtGui.QBrush(QtGui.QColor(color))
            )


def make_layout_tree_item(
    editor,
    data,
    base_make_tree_item=None
):
    """Create an editor tree item from ItemType metadata and capabilities."""
    kind = text_type(data.get("kind", "")).lower()
    definition = _definition(kind)
    type_title = definition.title if definition is not None else kind.title()

    tree_item = QtGui.QTreeWidgetItem([
        _tree_label(data),
        text_type(data.get("name", "")),
        type_title,
    ])
    editor.set_item_data(tree_item, kind, data["id"])

    flags = tree_item.flags()
    flags |= QtCore.Qt.ItemIsDragEnabled
    if definition is not None and definition.is_container:
        flags |= QtCore.Qt.ItemIsDropEnabled
    else:
        flags &= ~QtCore.Qt.ItemIsDropEnabled
    tree_item.setFlags(flags)
    _style_tree_item(tree_item, definition)

    if definition is not None and definition.is_container:
        for child in data.get("items", []) or []:
            tree_item.addChild(editor.make_tree_item(child))
        tree_item.setExpanded(True)

    return tree_item


def fix_layout_tree_structure(editor):
    """Normalize the tree using section/container/layout capabilities."""
    role_kind = QtCore.Qt.UserRole

    index = 0
    while index < editor.tree.topLevelItemCount():
        item = editor.tree.topLevelItem(index)
        kind = editor.item_data(item, role_kind)
        if _is_section(kind):
            index += 1
            continue

        orphan = editor.tree.takeTopLevelItem(index)
        target = _ensure_root_section(editor)
        if target is orphan:
            editor.tree.insertTopLevelItem(index, orphan)
            index += 1
            continue
        target.addChild(orphan)
        target.setExpanded(True)

    def normalize_container(container, nearest_section):
        container_kind = editor.item_data(container, role_kind)
        child_index = 0

        while child_index < container.childCount():
            child = container.child(child_index)
            child_kind = editor.item_data(child, role_kind)

            if not _can_contain(container_kind, child_kind):
                moved = container.takeChild(child_index)
                target = nearest_section or _ensure_root_section(editor)
                target.addChild(moved)
                target.setExpanded(True)
                if _is_container(child_kind):
                    normalize_container(
                        moved,
                        moved if _is_section(child_kind) else target
                    )
                continue

            child_definition = _definition(child_kind)
            if child_definition is not None and child_definition.is_container:
                normalize_container(
                    child,
                    child if child_definition.has_capability("section")
                    else nearest_section
                )
                child_index += 1
                continue

            while child.childCount():
                nested = child.takeChild(0)
                nested_kind = editor.item_data(nested, role_kind)
                if _can_contain(container_kind, nested_kind):
                    container.insertChild(child_index + 1, nested)
                    child_index += 1
                else:
                    target = nearest_section or _ensure_root_section(editor)
                    target.addChild(nested)
                    target.setExpanded(True)

            child_index += 1

    for root_index in range(editor.tree.topLevelItemCount()):
        root = editor.tree.topLevelItem(root_index)
        root_kind = editor.item_data(root, role_kind)
        if _is_container(root_kind):
            normalize_container(root, root if _is_section(root_kind) else None)


def sync_layout_working_from_tree(editor):
    """Serialize the current capability-valid tree into the v21 envelope."""
    if editor.current_property_editor is not None:
        try:
            editor.current_property_editor.write_to_item()
        except Exception:
            pass

    role_kind = QtCore.Qt.UserRole
    role_id = QtCore.Qt.UserRole + 1

    def data_from_tree(tree_item):
        item_id = editor.item_data(tree_item, role_id)
        kind = editor.item_data(tree_item, role_kind)

        data = editor.item_cache.get(item_id)
        if data is None:
            data = create_item(
                kind,
                {
                    "id": item_id,
                    "name": text_type(tree_item.text(1)),
                    "ui": {"label": text_type(tree_item.text(0))},
                }
            )

        data["kind"] = kind
        data["name"] = text_type(tree_item.text(1))
        data.setdefault("ui", {})["label"] = text_type(tree_item.text(0))
        definition = _definition(kind)

        if definition is not None and definition.is_container:
            children = []
            for child_index in range(tree_item.childCount()):
                child = tree_item.child(child_index)
                child_kind = editor.item_data(child, role_kind)
                if not _can_contain(kind, child_kind):
                    continue
                children.append(data_from_tree(child))
            data["items"] = children
        else:
            data.pop("items", None)

        return data

    sections = []
    for index in range(editor.tree.topLevelItemCount()):
        root_item = editor.tree.topLevelItem(index)
        root_kind = editor.item_data(root_item, role_kind)
        if not _is_section(root_kind):
            continue
        sections.append(data_from_tree(root_item))

    editor.working = {
        "version": CONFIG_VERSION,
        "sections": sections,
    }
    editor.rebuild_cache()


def _insert_under(editor, parent, tree_item, data_kind):
    role_kind = QtCore.Qt.UserRole
    if parent is not None:
        parent_kind = editor.item_data(parent, role_kind)
        if _can_contain(parent_kind, data_kind):
            parent.addChild(tree_item)
            parent.setExpanded(True)
            return tree_item

    if _is_section(data_kind):
        editor.tree.addTopLevelItem(tree_item)
        return tree_item

    root = _ensure_root_section(editor)
    root.addChild(tree_item)
    root.setExpanded(True)
    return tree_item


def insert_layout_cloned_tree_item(
    editor,
    data,
    sibling=False
):
    """Insert a cloned subtree according to capability-based containment."""
    tree_item = editor.make_tree_item(data)
    editor._cache_subtree(data)
    current = editor.tree.currentItem()
    kind = text_type(data.get("kind", "")).lower()

    if current is None:
        return _insert_under(editor, None, tree_item, kind)

    role_kind = QtCore.Qt.UserRole
    current_kind = editor.item_data(current, role_kind)
    parent = current.parent()

    if sibling:
        if parent is None:
            if _is_section(kind):
                index = editor.tree.indexOfTopLevelItem(current)
                editor.tree.insertTopLevelItem(index + 1, tree_item)
                return tree_item
            return _insert_under(editor, current, tree_item, kind)

        parent_kind = editor.item_data(parent, role_kind)
        if _can_contain(parent_kind, kind):
            index = parent.indexOfChild(current)
            parent.insertChild(index + 1, tree_item)
            return tree_item
        return _insert_under(
            editor,
            _nearest_section(editor, parent),
            tree_item,
            kind
        )

    if _can_contain(current_kind, kind):
        current.addChild(tree_item)
        current.setExpanded(True)
        return tree_item

    if parent is not None:
        parent_kind = editor.item_data(parent, role_kind)
        if _can_contain(parent_kind, kind):
            index = parent.indexOfChild(current)
            parent.insertChild(index + 1, tree_item)
            return tree_item

    return _insert_under(
        editor,
        _nearest_section(editor, current),
        tree_item,
        kind
    )


def create_layout_from_palette(
    editor,
    palette_item,
    column=0
):
    """Create an item using only registry containment semantics."""
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
        current_kind = editor.item_data(current, role_kind)
        if _can_contain(current_kind, kind):
            parent = current
        else:
            current_parent = current.parent()
            if current_parent is not None:
                parent_kind = editor.item_data(current_parent, role_kind)
                if _can_contain(parent_kind, kind):
                    parent = current_parent
            if parent is None:
                parent = _nearest_section(editor, current)

    if parent is None and not _is_section(kind):
        parent = _ensure_root_section(editor)

    _insert_under(editor, parent, tree_item, kind)
    editor.tree.setCurrentItem(tree_item)
    editor.fix_tree_structure()
    editor.tree_changed()


def delete_layout_selected(
    editor,
    base_delete_selected
):
    """Confirm destructive container deletion, then use the base removal path."""
    item = editor.tree.currentItem()
    if item is None:
        return

    kind = editor.item_data(item, QtCore.Qt.UserRole)
    definition = _definition(kind)

    if (
        definition is not None and
        definition.is_container and
        item.childCount()
    ):
        answer = QtGui.QMessageBox.question(
            editor,
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

    return base_delete_selected(editor)


__all__ = [
    "create_layout_from_palette",
    "delete_layout_selected",
    "fix_layout_tree_structure",
    "insert_layout_cloned_tree_item",
    "make_layout_tree_item",
    "sync_layout_working_from_tree",
]
