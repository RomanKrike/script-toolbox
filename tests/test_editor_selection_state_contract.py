# -*- coding: utf-8 -*-

import os


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


def _read(relative_path):
    path = os.path.join(
        ROOT,
        *relative_path.split("/")
    )
    with open(path, "r") as handle:
        return handle.read()


def test_editor_tree_branch_highlight_uses_shared_dark_selection_color():
    source = _read(
        "scripts/script_toolbox/ui/editor_selection_state.py"
    )

    assert "SELECTION_BG" in source
    assert "QtGui.QPalette.Highlight" in source
    assert "QtGui.QPalette.HighlightedText" in source
    assert "show-decoration-selected: 1" in source
    assert "QTreeWidget::branch:selected" in source
    assert "selection-background-color: %s" in source
    assert "background-color: %s" in source
    assert "_apply_selection_palette(\n            self.palette" in source
    assert "_apply_selection_palette(\n            self.tree" in source


def test_apply_preserves_selected_property_and_description_scroll_position():
    source = _read(
        "scripts/script_toolbox/ui/editor_selection_state.py"
    )

    assert "current_id = self.current_item_id" in source
    assert "scroll_value = _property_scroll_value" in source
    assert "selected = self.tree_item_by_id" in source
    assert "self.tree.setCurrentItem" in source
    assert "QtCore.QTimer.singleShot" in source
    assert "_restore_property_scroll" in source


def test_editor_selection_state_hook_is_installed_before_adapter_wrapping():
    source = _read(
        "scripts/script_toolbox/ui/__init__.py"
    )

    install_index = source.index(
        "install_editor_selection_state(_interface_editor_module.InterfaceEditor)"
    )
    adapter_index = source.index(
        "InterfaceEditor = build_interface_editor_class("
    )

    assert install_index < adapter_index
