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
    assert "_hide_palette_hint(" in source
    assert '"HintText"' in source
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


def test_icon_only_button_uses_real_centered_child_layout():
    source = _read(
        "scripts/script_toolbox/ui/editor_polish_hooks.py"
    )
    ui_source = _read(
        "scripts/script_toolbox/ui/__init__.py"
    )

    assert 'bool(item.get("icon_only", False))' in source
    assert "_install_centered_button_icon(" in source
    assert "button.setIcon(" in source
    assert "QtGui.QIcon()" in source
    assert "QtGui.QHBoxLayout(" in source
    assert '"ScriptButtonCenteredIcon"' in source
    assert "layout.addStretch(1)" in source
    assert "QtCore.Qt.AlignCenter" in source
    assert "QtCore.Qt.WA_TransparentForMouseEvents" in source
    assert "install_editor_search_ux(" in ui_source
    assert "install_icon_only_button_centering(" in ui_source
    assert ui_source.index(
        "install_event_binding_hooks("
    ) < ui_source.index(
        "install_icon_only_button_centering("
    )
