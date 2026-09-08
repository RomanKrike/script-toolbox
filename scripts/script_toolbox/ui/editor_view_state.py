# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore
from ..pycompat import text_type


ROLE_ID = QtCore.Qt.UserRole + 1


def build_editor_view_state_class(base_class):
    """Preserve Interface Editor view state across Apply rebuilds."""

    class InterfaceEditor(base_class):

        def _capture_tree_view_state(self):
            expanded = {}

            def visit(tree_item):
                item_id = self.item_data(
                    tree_item,
                    ROLE_ID
                )
                if item_id:
                    expanded[text_type(item_id)] = bool(
                        tree_item.isExpanded()
                    )

                for index in range(
                    tree_item.childCount()
                ):
                    visit(
                        tree_item.child(index)
                    )

            for index in range(
                self.tree.topLevelItemCount()
            ):
                visit(
                    self.tree.topLevelItem(index)
                )

            current = self.tree.currentItem()
            current_id = (
                self.item_data(
                    current,
                    ROLE_ID
                )
                if current is not None
                else self.current_item_id
            )

            state = {
                "current_id": text_type(current_id or ""),
                "expanded": expanded,
                "tree_vertical_scroll": 0,
                "tree_horizontal_scroll": 0,
                "property_vertical_scroll": 0,
            }

            try:
                state["tree_vertical_scroll"] = int(
                    self.tree.verticalScrollBar().value()
                )
                state["tree_horizontal_scroll"] = int(
                    self.tree.horizontalScrollBar().value()
                )
            except Exception:
                pass

            try:
                state["property_vertical_scroll"] = int(
                    self.property_scroll.verticalScrollBar().value()
                )
            except Exception:
                pass

            return state

        def _restore_tree_view_state(self, state):
            if not state:
                return

            expanded = state.get(
                "expanded",
                {}
            )

            def visit(tree_item):
                item_id = self.item_data(
                    tree_item,
                    ROLE_ID
                )
                item_id = text_type(
                    item_id or ""
                )
                if item_id in expanded:
                    tree_item.setExpanded(
                        bool(expanded[item_id])
                    )

                for index in range(
                    tree_item.childCount()
                ):
                    visit(
                        tree_item.child(index)
                    )

            for index in range(
                self.tree.topLevelItemCount()
            ):
                visit(
                    self.tree.topLevelItem(index)
                )

            current_id = text_type(
                state.get("current_id", "") or ""
            )
            if current_id:
                selected = self.tree_item_by_id(
                    current_id
                )
                if selected is not None:
                    self.tree.setCurrentItem(
                        selected
                    )

            try:
                self.tree.verticalScrollBar().setValue(
                    int(state.get("tree_vertical_scroll", 0))
                )
                self.tree.horizontalScrollBar().setValue(
                    int(state.get("tree_horizontal_scroll", 0))
                )
            except Exception:
                pass

            try:
                self.property_scroll.verticalScrollBar().setValue(
                    int(state.get("property_vertical_scroll", 0))
                )
            except Exception:
                pass

        def apply_changes(self):
            view_state = self._capture_tree_view_state()
            result = base_class.apply_changes(self)
            if result:
                self._restore_tree_view_state(
                    view_state
                )
            return result

    InterfaceEditor.__name__ = "InterfaceEditor"
    return InterfaceEditor


__all__ = [
    "build_editor_view_state_class",
]
