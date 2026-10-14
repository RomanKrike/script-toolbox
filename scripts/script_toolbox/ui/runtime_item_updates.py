# -*- coding: utf-8 -*-
"""Surface-owned Item presentations and targeted replacement fallback."""
from __future__ import print_function

from ..compat import QtCore, QtGui
from ..core.item_changes import resolve_item
from ..model.item_registry import ITEM_TYPES


class RuntimeItemUpdates(object):
    def __init__(self, context):
        self.context = context
        self.entries = {}

    def register(self, item, widget, owner, compact):
        item_id = item["id"]
        self.entries[item_id] = (widget, owner, compact)

        def destroyed(*args):
            entry = self.entries.get(item_id)
            if entry is not None and entry[0] is widget:
                self.entries.pop(item_id, None)
        widget.destroyed.connect(destroyed)

    def apply(self, item, change):
        entry = self.entries.get(item["id"])
        if entry is None:
            # Grouped Folder pages have their own presentation owner.
            if ITEM_TYPES.get(item["kind"]).is_container:
                self.context._window.rebuild()
            return
        root, owner, compact = entry
        callback = getattr(root, "apply_item_change", None)
        if callable(callback) and callback(item, change):
            self.context.conditions.refresh()
            return
        remaining = set(change.fields)
        if "ui.tooltip" in remaining:
            self.context.conditions.update_tooltip(item["id"], item["ui"]["tooltip"])
            remaining.remove("ui.tooltip")
        remaining.difference_update(("ui.visible", "ui.enabled", "ui.visible_expression",
                                    "ui.enabled_expression", "ui.visible_expression_enabled",
                                    "ui.enabled_expression_enabled"))
        if item["kind"] == "image":
            from .image_item import update_image
            update_image(root, item)
            remaining.difference_update("props." + name for name in ITEM_TYPES.get("image").fields)
        if "ui.label" in remaining:
            label = getattr(root, "_item_label", None)
            if label is None and item["kind"] in ("button", "label", "checkbox"):
                label = root if callable(getattr(root, "setText", None)) else None
            if label is not None:
                label.setText(item["ui"]["label"] if item["ui"].get("show_label", True) else "")
                remaining.remove("ui.label")
        value_fields = set(["props.value"])
        if item["kind"] in ("integer", "float"):
            value_fields.update(("props.min", "props.max"))
        if item["kind"] == "color":
            value_fields.update("props." + name for name in ITEM_TYPES.get("color").fields)
        if item["kind"] == "menu":
            value_fields.add("props.items")
        if remaining and remaining.issubset(value_fields):
            if self.context._window.sync_runtime_value(item["id"]):
                return
        if not remaining:
            return
        # Layout metadata is applied by the immediate layout container renderer.
        layout_fields = set("ui." + name for name in (
            "width_mode", "width", "stretch", "height_mode", "height", "vertical_stretch"))
        if remaining.intersection(layout_fields):
            parent = root.parentWidget()
            parent_entry = next((pair for pair in self.entries.items() if pair[1][0] is parent), None)
            if parent_entry is not None:
                parent_item = resolve_item(self.context.config, parent_entry[0])
                if ITEM_TYPES.get(parent_item["kind"]).is_layout:
                    self._replace(parent_item, parent_entry[1])
                    return
        if remaining == set(["ui.horizontal_alignment"]):
            parent = root.parentWidget()
            if parent is not None and parent.objectName() == "RuntimeFolderContent":
                flags = {"left": QtCore.Qt.AlignLeft, "center": QtCore.Qt.AlignHCenter,
                         "right": QtCore.Qt.AlignRight}
                parent.layout().setAlignment(root, flags.get(item["ui"]["horizontal_alignment"], QtCore.Qt.Alignment(0)))
            return
        self._replace(item, entry)

    def _replace(self, item, entry):
        from .runtime_renderers import get_runtime_renderer_registry
        old, owner, compact = entry
        parent = old.parentWidget()
        layout = parent.layout() if parent is not None else None
        index = layout.indexOf(old) if layout is not None else -1
        if index < 0 or not isinstance(layout, QtGui.QBoxLayout):
            self.context._window.rebuild()
            return
        # Preserve layout placement and focus while replacing only this subtree.
        alignment = layout.itemAt(index).alignment()
        stretch = layout.stretch(index)
        focused = old.hasFocus() or any(child.hasFocus() for child in old.findChildren(QtGui.QWidget))
        new = get_runtime_renderer_registry().render(owner, item, compact=compact)
        if new is None:
            raise RuntimeError("No renderer for Item " + item["kind"])
        layout.takeAt(index)
        layout.insertWidget(index, new, stretch, alignment)
        # Parent layouts can have imposed sizes/policies on the child.
        if not ITEM_TYPES.get(item["kind"]).is_layout:
            new.setSizePolicy(old.sizePolicy())
            new.setMinimumSize(old.minimumSize())
            new.setMaximumSize(old.maximumSize())
        old.hide()
        old.deleteLater()
        if focused:
            new.setFocus()
        self.context.conditions.refresh()

    def dispose(self):
        self.entries.clear()
        self.context = None
