# -*- coding: utf-8 -*-
from __future__ import print_function

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_create_and_existing_search_fields_live_at_column_bottoms():
    source = _read(
        "scripts/script_toolbox/ui/editor_polish_hooks.py"
    )

    remove_index = source.index(
        "palette_layout.removeWidget("
    )
    add_index = source.index(
        "palette_layout.addWidget("
    )

    assert remove_index < add_index
    assert '"ExistingParametersFilter"' in source
    assert '"Filter existing parameters..."' in source
    assert "tree_layout.addWidget(" in source
    assert "self.filter_existing_parameters" in source
    assert "_filter_tree_branch(" in source
    assert "child_match" in source


def test_existing_parameter_filter_is_reapplied_after_tree_rebuild():
    source = _read(
        "scripts/script_toolbox/ui/editor_polish_hooks.py"
    )

    populate_source = source.split(
        "    def populate_tree(self):",
        1
    )[1].split(
        "    editor_class.filter_existing_parameters",
        1
    )[0]

    assert "original_populate_tree(self)" in populate_source
    assert "self.filter_existing_parameters(" in populate_source


def test_icon_only_button_overrides_left_aligned_runtime_style():
    source = _read(
        "scripts/script_toolbox/ui/editor_polish_hooks.py"
    )
    ui_source = _read(
        "scripts/script_toolbox/ui/__init__.py"
    )

    assert 'bool(item.get("icon_only", False))' in source
    assert "button.setText(\"\")" in source
    assert "text-align: center;" in source
    assert "padding-left: 0px;" in source
    assert "padding-right: 0px;" in source
    assert "install_editor_search_ux(" in ui_source
    assert "install_icon_only_button_centering(" in ui_source
    assert ui_source.index(
        "install_event_binding_hooks("
    ) < ui_source.index(
        "install_icon_only_button_centering("
    )
