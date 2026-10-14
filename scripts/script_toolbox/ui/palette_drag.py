# -*- coding: utf-8 -*-
"""Copy-only palette drags and capability-valid editor insertion."""
from __future__ import print_function

import json

from ..compat import QtCore, QtGui
from ..core.presets import build_preset_root
from ..core.preset_references import iter_targets
from ..model.items import create_item
from ..model.item_registry import ITEM_TYPES
from .layout_editor_adapter import _can_contain, _is_section

PALETTE_MIME = "application/x-script-toolbox-create-item"


def palette_source(editor, item, presets=False):
    if item is None:
        return None
    if not presets:
        kind = editor.palette_item_kind(item)
        definition = ITEM_TYPES.get(kind) if kind else None
        return {"kind": kind} if definition is not None else None
    from .managed_presets import library_address, target_address
    from .preset_hooks import ROLE_PRESET_ID, _role_text
    address = library_address(item)
    if address:
        return {"library": address}
    address = target_address(item)
    if address:
        return {"target": address}
    preset = _role_text(item, ROLE_PRESET_ID)
    return {"preset": preset} if preset else None


def source_data(editor, source):
    if "kind" in source:
        return create_item(source["kind"])
    if "preset" in source:
        return build_preset_root(source["preset"])
    address = source.get("library") or source.get("target")
    package = editor.preset_resolver.packages.get(address[0])
    if package is None:
        return None
    preset = next((p for p in package["presets"] if p["id"] == address[1]), None)
    if preset is None:
        return None
    if "target" in source:
        return next((p for p in iter_targets(preset["root"]) if p["id"] == address[2]), None)
    return preset["root"]


class CreationPaletteTree(QtGui.QTreeWidget):
    def __init__(self, editor, parent=None, presets=False):
        QtGui.QTreeWidget.__init__(self, parent)
        self.editor = editor
        self.presets = presets
        self.setDragEnabled(True)
        self.setDragDropMode(QtGui.QAbstractItemView.DragOnly)

    def supportedDropActions(self):
        return QtCore.Qt.CopyAction

    def mimeData(self, items):
        if len(items) != 1:
            return None
        source = palette_source(self.editor, items[0], self.presets)
        if source is None:
            return None
        mime = QtGui.QTreeWidget.mimeData(self, items)
        mime.setData(PALETTE_MIME, json.dumps(source).encode("utf-8"))
        return mime

    def startDrag(self, actions):
        if palette_source(self.editor, self.currentItem(), self.presets) is not None:
            QtGui.QTreeWidget.startDrag(self, QtCore.Qt.CopyAction)


def drop_location(tree, target, position, kind):
    """Return (parent, index); reject leaf, reference and invalid root drops."""
    editor = tree.editor
    if position == QtGui.QAbstractItemView.OnViewport or target is None:
        parent, index = None, tree.topLevelItemCount()
    elif position == QtGui.QAbstractItemView.OnItem:
        parent, index = target, target.childCount()
    else:
        parent = target.parent()
        index = parent.indexOfChild(target) if parent is not None else tree.indexOfTopLevelItem(target)
        if position == QtGui.QAbstractItemView.BelowItem:
            index += 1
    if parent is None:
        return (parent, index) if _is_section(kind) else None
    if not _can_contain(editor.item_data(parent, QtCore.Qt.UserRole), kind):
        return None
    ancestor = parent
    while ancestor is not None:
        data = editor.item_cache.get(editor.item_data(ancestor, QtCore.Qt.UserRole + 1), {})
        if data.get("kind") == "reference" or data.get("_preset_reference"):
            return None
        ancestor = ancestor.parent()
    return parent, index


def insert_palette_drop(editor, source, parent, index):
    data = source_data(editor, source)
    if data is None:
        return None
    # Flush pending property edits before taking the document delta.
    if editor.history_timer.isActive():
        editor.commit_history()
    editor.sync_working_from_tree()
    clone = editor._clone_data(data, editor._used_names())
    tree_item = editor.make_tree_item(clone)
    editor._cache_subtree(clone)
    if parent is None:
        editor.tree.insertTopLevelItem(index, tree_item)
    else:
        parent.insertChild(index, tree_item)
        parent.setExpanded(True)
    tree_item.setExpanded(True)
    editor.tree.setCurrentItem(tree_item)
    editor.tree_changed()
    return tree_item


def drag_source(tree, event):
    source = event.source()
    if not isinstance(source, CreationPaletteTree) or source.editor is not tree.editor:
        return None
    if not event.mimeData().hasFormat(PALETTE_MIME):
        return None
    try:
        value = bytes(event.mimeData().data(PALETTE_MIME)).decode("utf-8")
        descriptor = json.loads(value)
        data = source_data(tree.editor, descriptor)
        return (descriptor, data["kind"]) if data else None
    except (ValueError, KeyError, TypeError):
        return None


def event_position(event):
    return event.position().toPoint() if hasattr(event, "position") else event.pos()
