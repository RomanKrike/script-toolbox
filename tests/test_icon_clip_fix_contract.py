# -*- coding: utf-8 -*-

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_close_controls_bypass_qtoolbutton_style_geometry():
    source = _read(
        "scripts/script_toolbox/ui/icon_clip_fix.py"
    )

    assert "class PaintedIconButton(QtGui.QWidget):" in source
    assert "self._icon.paint(" in source
    assert "self._icon_rect()" in source
    assert "QtGui.QToolButton" not in source
    assert 'builtin_icon("close")' in source
    assert 'builtin_icon("add")' in source
    assert 'builtin_icon("find")' in source


def test_search_clear_uses_painted_child_inside_line_edit():
    source = _read(
        "scripts/script_toolbox/ui/icon_clip_fix.py"
    )

    assert "parent=line_edit" in source
    assert "clear_button.clicked.connect(line_edit.clear)" in source
    assert "line_edit.setTextMargins(" in source
    assert "polish_module._search_control = _painted_search_control" in source


def test_trigger_close_and_add_methods_are_replaced_before_instances():
    source = _read(
        "scripts/script_toolbox/ui/icon_clip_fix.py"
    )
    ui_source = _read(
        "scripts/script_toolbox/ui/__init__.py"
    )

    assert "TriggerTabBindingPanel._install_trigger_close_button" in source
    assert "TriggerTabBindingPanel._ensure_add_button" in source
    assert "install_icon_clip_fix()" in ui_source
    assert ui_source.index(
        "install_editor_search_ux("
    ) < ui_source.index(
        "install_icon_clip_fix()"
    )
