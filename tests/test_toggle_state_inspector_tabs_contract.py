# -*- coding: utf-8 -*-

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_toggle_state_tabs_stay_accessible_and_share_inspector_style():
    for relative_path in (
        "scripts/script_toolbox/ui/properties/toggle_button.py",
        "scripts/script_toolbox/ui/properties/toggle_icon.py",
    ):
        source = _read(relative_path)
        assert "from .inspector_tabs import style_inspector_tabs" in source
        assert "style_inspector_tabs(self.state_tabs)" in source
        assert "self.state_tabs.setTabEnabled(0, True)" in source
        assert "self.state_get_editor.setEnabled(True)" in source
        assert "setTabEnabled(0, scripted)" not in source


def test_trigger_panel_has_no_redundant_events_group_box_chrome():
    source = _read(
        "scripts/script_toolbox/ui/properties/bindings.py"
    )

    assert "from .inspector_tabs import style_binding_panel" in source
    assert "from .inspector_tabs import style_inspector_tabs" in source
    assert 'QtGui.QGroupBox.__init__(self, "", parent)' in source
    assert "style_binding_panel(self)" in source
    assert "style_inspector_tabs(self.tabs)" in source
    assert 'QtGui.QGroupBox.setTitle(self, "")' in source


def test_inspector_tabs_reuse_runtime_tab_palette_and_metrics():
    source = _read(
        "scripts/script_toolbox/ui/properties/inspector_tabs.py"
    )

    for expected in (
        "FOLDER_CARD_BG",
        "FOLDER_HEADER_HOVER_BG",
        "SEPARATOR",
        "TEXT_FOLDER_COLLAPSED",
        "TEXT_FOLDER_HOVER",
        "TEXT_HEADING",
        "WINDOW_BG",
        "RUNTIME_TAB_MIN_HEIGHT",
        "RUNTIME_TAB_PADDING_VERTICAL",
        "RUNTIME_TAB_PADDING_HORIZONTAL",
        "RUNTIME_TAB_BAR_OFFSET",
        "RUNTIME_TAB_BAR_VERTICAL_OFFSET",
        "RUNTIME_TAB_PANE_TOP_OFFSET",
        "RUNTIME_TAB_SELECTED_OVERLAP",
    ):
        assert expected in source

    assert "QTabWidget#InspectorTabs::pane" in source
    assert "QTabWidget#InspectorTabs QTabBar::tab:selected" in source
    assert "QGroupBox#TriggerBindingPanel" in source
