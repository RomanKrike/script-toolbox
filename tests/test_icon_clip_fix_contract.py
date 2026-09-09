# -*- coding: utf-8 -*-

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_clip_sensitive_controls_use_shared_painted_icon_component():
    source = _read(
        "scripts/script_toolbox/ui/icon_clip_fix.py"
    )
    painted_source = _read(
        "scripts/script_toolbox/ui/painted_icon_button.py"
    )

    assert "from .painted_icon_button import PaintedIconButton" in source
    assert "class PaintedIconButton(QtGui.QWidget):" in painted_source
    assert "self._icon.paint(" in painted_source
    assert "self._icon_rect()" in painted_source
    assert "QtGui.QToolButton" not in painted_source
    assert 'builtin_icon("close")' in source
    assert 'builtin_icon("add")' in source


def test_search_clip_workaround_is_owned_by_search_field_not_monkeypatch():
    source = _read(
        "scripts/script_toolbox/ui/icon_clip_fix.py"
    )
    search_source = _read(
        "scripts/script_toolbox/ui/search_field.py"
    )

    assert "PaintedIconButton(" in search_source
    assert 'builtin_icon("find")' in search_source
    assert 'builtin_icon("close")' in search_source
    assert "self.clear_button.clicked.connect(" in search_source
    assert "self.setTextMargins(" in search_source

    assert "editor_polish_hooks" not in source
    assert "polish_module" not in source
    assert "_search_control" not in source
    assert "SearchDecorationFilter" not in source


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
    assert "TriggerTabBindingPanel,\n        _INSTALL_MARKER" in source
