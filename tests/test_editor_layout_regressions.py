# -*- coding: utf-8 -*-

import os


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


def _source(*parts):
    path = os.path.join(
        ROOT,
        *parts
    )
    with open(path, "r") as handle:
        return handle.read()


def test_apply_view_state_wrapper_is_installed():
    ui_init = _source(
        "scripts",
        "script_toolbox",
        "ui",
        "__init__.py"
    )
    view_state = _source(
        "scripts",
        "script_toolbox",
        "ui",
        "editor_view_state.py"
    )

    assert "build_editor_view_state_class" in ui_init
    assert "_capture_tree_view_state" in view_state
    assert "_restore_tree_view_state" in view_state
    assert '"current_id"' in view_state
    assert '"expanded"' in view_state
    assert "base_class.apply_changes(self)" in view_state


def test_row_gives_nested_layouts_cross_axis_height():
    row_runtime = _source(
        "scripts",
        "script_toolbox",
        "ui",
        "row_layout.py"
    )

    assert "_layout_child_fills_height" in row_runtime
    assert '"column"' in row_runtime
    assert "QtGui.QSizePolicy.Expanding" in row_runtime
    assert "if fill_height:" in row_runtime


def test_column_requests_expandable_vertical_space():
    column_runtime = _source(
        "scripts",
        "script_toolbox",
        "ui",
        "column_layout.py"
    )

    assert 'widget.setObjectName("RuntimeColumn")' in column_runtime
    assert "QtGui.QSizePolicy.Preferred" in column_runtime
    assert "QtGui.QSizePolicy.Expanding" in column_runtime
    assert '"vertical_distribution"' in column_runtime
