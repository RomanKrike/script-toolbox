# -*- coding: utf-8 -*-
from __future__ import print_function

from ..pycompat import text_type
from .editor_scroll_frames import install_interface_editor_scroll_frames
from .property_pane_style import apply_property_pane_style
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


def filter_existing_parameters(editor, value):
    """Filter the Existing Interface tree while preserving matching parents."""
    query = text_type(
        value or ""
    ).strip().lower()

    for index in range(
        editor.tree.topLevelItemCount()
    ):
        _filter_tree_branch(
            editor.tree.topLevelItem(index),
            query
        )


def reapply_existing_filter(editor):
    """Reapply the active structure filter after a tree rebuild."""
    search = getattr(
        editor,
        "existing_filter",
        None
    )
    if search is not None:
        filter_existing_parameters(
            editor,
            search.text()
        )


def apply_editor_presentation(editor):
    """Apply presentation policies after the editor builds its own controls."""
    apply_property_pane_style(editor)
    install_interface_editor_scroll_frames(editor)


def build_search_interface_editor_class(base_class):
    """Compatibility wrapper for older direct builder imports.

    Active Script Toolbox composition builds SearchField controls in the base
    editor and applies presentation helpers from the document adapter. This
    wrapper remains only for older callers that still use the builder API.
    """

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
            apply_editor_presentation(self)

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

        def filter_existing_parameters(self, value):
            return filter_existing_parameters(
                self,
                value
            )

        def populate_tree(self):
            base_class.populate_tree(
                self
            )
            reapply_existing_filter(self)

    InterfaceEditor.__name__ = "InterfaceEditor"
    return InterfaceEditor


__all__ = [
    "apply_editor_presentation",
    "build_search_interface_editor_class",
    "filter_existing_parameters",
    "reapply_existing_filter",
]
