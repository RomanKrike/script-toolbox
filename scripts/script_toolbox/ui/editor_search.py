# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtGui
from ..pycompat import text_type
from .editor_scroll_frames import install_interface_editor_scroll_frames
from .property_pane_style import apply_property_pane_style
from .search_field import SearchField
from .share_hooks import install_share_controller


def _tree_item_matches(item, query):
    if not query:
        return True

    values = []
    for column in range(3):
        try:
            values.append(
                text_type(item.text(column)).lower()
            )
        except Exception:
            pass

    try:
        values.append(
            text_type(item.toolTip(0)).lower()
        )
    except Exception:
        pass

    return any(
        query in value
        for value in values
    )


def _filter_tree_branch(item, query):
    child_match = False

    for child_index in range(item.childCount()):
        child = item.child(child_index)
        if _filter_tree_branch(child, query):
            child_match = True

    visible = (
        _tree_item_matches(item, query) or
        child_match
    )
    item.setHidden(not visible)

    if query and child_match:
        item.setExpanded(True)

    return visible


def _hide_legacy_palette_hint(parent):
    """Preserve the current editor layout while the base dialog is split up."""
    try:
        labels = parent.findChildren(
            QtGui.QLabel
        )
    except Exception:
        labels = []

    for label in labels:
        try:
            if text_type(label.objectName()) == "HintText":
                label.hide()
                return
        except Exception:
            pass


def build_search_interface_editor_class(base_class):
    """Add search, presentation policies and composed editor features."""

    class InterfaceEditor(base_class):

        def __init__(self, toolbox, parent=None):
            # Share must exist before the legacy constructor calls build_ui(),
            # where _icon_button() is resolved dynamically on this instance.
            install_share_controller(self)
            base_class.__init__(
                self,
                toolbox,
                parent=parent
            )

        def build_ui(self):
            base_class.build_ui(
                self
            )
            self._install_search_fields()
            apply_property_pane_style(self)
            install_interface_editor_scroll_frames(self)

        # --------------------------------------------------------------
        # Explicit feature composition
        # --------------------------------------------------------------

        def _icon_button(
            self,
            icon_name,
            tooltip,
            callback
        ):
            return self.share_controller.icon_button(
                icon_name,
                tooltip,
                callback
            )

        def show_tree_context_menu(self, point):
            return self.share_controller.show_tree_context_menu(
                point
            )

        def share_settings(self):
            return self.share_controller.share_settings()

        def paste_shared_settings(self):
            return self.share_controller.paste_shared_settings()

        def share_selected(self, target_item=None):
            return self.share_controller.share_selected(
                target_item
            )

        def paste_shared_selected(self):
            return self.share_controller.paste_shared_selected()

        # --------------------------------------------------------------
        # Search
        # --------------------------------------------------------------

        def _install_search_fields(self):
            self.search_fields = {}

            # The legacy dialog creates PaletteFilter above the tree. The
            # active polished UI has the search control below the tree, so
            # replace that legacy field while preserving the current layout.
            old_filter = getattr(
                self,
                "palette_filter",
                None
            )
            palette_parent = None
            palette_layout = None
            try:
                palette_parent = self.palette.parentWidget()
                palette_layout = palette_parent.layout()
            except Exception:
                pass

            if palette_layout is not None:
                old_text = ""
                if old_filter is not None:
                    try:
                        old_text = text_type(
                            old_filter.text() or ""
                        )
                    except Exception:
                        pass
                    try:
                        palette_layout.removeWidget(
                            old_filter
                        )
                        old_filter.setParent(None)
                        old_filter.deleteLater()
                    except Exception:
                        pass

                _hide_legacy_palette_hint(
                    palette_parent
                )
                self.palette_filter = SearchField(
                    "Filter parameters...",
                    parent=palette_parent
                )
                self.palette_filter.textChanged.connect(
                    self.filter_palette
                )
                if old_text:
                    self.palette_filter.setText(
                        old_text
                    )
                self.palette_search_control = self.palette_filter
                self.search_fields[
                    "palette"
                ] = self.palette_filter
                palette_layout.addWidget(
                    self.palette_filter
                )

            tree_parent = None
            tree_layout = None
            try:
                tree_parent = self.tree.parentWidget()
                tree_layout = tree_parent.layout()
            except Exception:
                pass

            if tree_layout is not None:
                self.existing_filter = SearchField(
                    "Filter existing parameters...",
                    parent=tree_parent
                )
                self.existing_filter.textChanged.connect(
                    self.filter_existing_parameters
                )
                self.existing_search_control = self.existing_filter
                self.search_fields[
                    "structure"
                ] = self.existing_filter
                tree_layout.addWidget(
                    self.existing_filter
                )

        def filter_existing_parameters(self, value):
            query = text_type(
                value or ""
            ).strip().lower()

            for index in range(
                self.tree.topLevelItemCount()
            ):
                _filter_tree_branch(
                    self.tree.topLevelItem(index),
                    query
                )

        def populate_tree(self):
            base_class.populate_tree(
                self
            )
            search = getattr(
                self,
                "existing_filter",
                None
            )
            if search is not None:
                self.filter_existing_parameters(
                    search.text()
                )

    InterfaceEditor.__name__ = "InterfaceEditor"
    return InterfaceEditor


__all__ = [
    "build_search_interface_editor_class",
]
