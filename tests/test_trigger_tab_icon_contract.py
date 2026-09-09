# -*- coding: utf-8 -*-

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_trigger_tabs_own_qt4_safe_painted_icon_controls():
    source = _read(
        "scripts/script_toolbox/ui/properties/trigger_tabs.py"
    )
    painted_source = _read(
        "scripts/script_toolbox/ui/painted_icon_button.py"
    )

    assert "from ..painted_icon_button import PaintedIconButton" in source
    assert "class PaintedIconButton(QtGui.QWidget):" in painted_source
    assert "self._icon.paint(" in painted_source
    assert "self._icon_rect()" in painted_source
    assert "QtGui.QToolButton" not in painted_source
    assert "QtGui.QToolButton" not in source
    assert 'builtin_icon("close")' in source
    assert 'builtin_icon("add")' in source


def test_trigger_close_geometry_preserves_maya_qt4_clip_contract():
    source = _read(
        "scripts/script_toolbox/ui/properties/trigger_tabs.py"
    )

    for definition in (
        "_TRIGGER_CLOSE_HOLDER_SIZE = (22, 20)",
        "_TRIGGER_CLOSE_BUTTON_SIZE = 18",
        "_TRIGGER_CLOSE_GLYPH_SIZE = 10",
        "_TRIGGER_CLOSE_OFFSET = (2, 1)",
    ):
        assert definition in source

    close_block = source.split(
        "def _install_trigger_close_button(self, page):",
        1
    )[1].split(
        "def _ensure_add_button(self):",
        1
    )[0]

    assert "PaintedIconButton(" in close_block
    assert "_TRIGGER_CLOSE_GLYPH_SIZE" in close_block
    assert "interactive=True" in close_block
    assert "hover_feedback=True" in close_block
    assert "*_TRIGGER_CLOSE_HOLDER_SIZE" in close_block
    assert "_TRIGGER_CLOSE_BUTTON_SIZE" in close_block
    assert "*_TRIGGER_CLOSE_OFFSET" in close_block
    assert "self.remove_binding(current)" in close_block


def test_trigger_add_geometry_and_tab_owned_click_behavior_are_preserved():
    source = _read(
        "scripts/script_toolbox/ui/properties/trigger_tabs.py"
    )

    for definition in (
        "_TRIGGER_ADD_BUTTON_SIZE = 16",
        "_TRIGGER_ADD_GLYPH_SIZE = 12",
        "_TRIGGER_ADD_SPACER_WIDTH = 12",
    ):
        assert definition in source

    add_block = source.split(
        "def _ensure_add_button(self):",
        1
    )[1].split(
        "def _install_add_tab_spacer(self, index):",
        1
    )[0]

    assert "PaintedIconButton(" in add_block
    assert "_TRIGGER_ADD_GLYPH_SIZE" in add_block
    assert "interactive=False" in add_block
    assert "hover_feedback=False" in add_block
    assert "_TRIGGER_ADD_BUTTON_SIZE" in add_block

    assert "watched.tabAt(" in source
    assert "QtCore.QTimer.singleShot(\n                        0,\n                        self.add_binding" in source
    assert "return _BaseBindingPanel.eventFilter(" in source


def test_icon_clip_monkeypatch_is_removed_from_active_ui():
    ui_source = _read(
        "scripts/script_toolbox/ui/__init__.py"
    )

    assert not (
        ROOT /
        "scripts/script_toolbox/ui/icon_clip_fix.py"
    ).exists()
    assert "icon_clip_fix" not in ui_source
    assert "install_icon_clip_fix" not in ui_source


def test_search_keeps_its_own_painted_icon_workaround():
    search_source = _read(
        "scripts/script_toolbox/ui/search_field.py"
    )

    assert "PaintedIconButton(" in search_source
    assert 'builtin_icon("find")' in search_source
    assert 'builtin_icon("close")' in search_source
    assert "self.clear_button.clicked.connect(" in search_source
    assert "self.setTextMargins(" in search_source
