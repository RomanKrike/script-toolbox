# -*- coding: utf-8 -*-

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_runtime_tabs_use_one_bar_owned_seam_compensation():
    metrics = _read("scripts/script_toolbox/style/metrics.py")
    overrides = _read("scripts/script_toolbox/style/runtime_overrides.py")
    runtime = _read("scripts/script_toolbox/ui/runtime.py")

    # Runtime and editor panes deliberately have separate vertical contracts.
    # Runtime keeps the pane and selected tab at their natural positions; the
    # tab bar alone moves down by one border width to cover the page-frame seam.
    assert "TAB_PANE_TOP_OFFSET = -1" in metrics
    assert "RUNTIME_TAB_BAR_VERTICAL_OFFSET = TAB_BORDER_WIDTH" in metrics
    assert "RUNTIME_TAB_PANE_TOP_OFFSET = 0" in metrics
    assert "RUNTIME_TAB_SELECTED_OVERLAP = 0" in metrics
    assert "RUNTIME_TAB_BAR_VERTICAL_OFFSET" in overrides
    assert "top: {runtime_tab_bar_vertical_offset}px;" in overrides
    assert "top: {runtime_tab_pane_top_offset}px;" in overrides
    assert "top: {tab_pane_top_offset}px;" in overrides

    # QTabWidget::pane is layout-only at runtime. The visible rounded outline
    # belongs to the existing RuntimeFolder tab page instead, avoiding the
    # host-dependent rounded-subcontrol clipping seen in Houdini/Qt5.
    assert 'self.setProperty("folderType", self.folder_type)' in runtime
    assert (
        "QWidget#ToolboxContent QTabWidget::pane {{\n"
        "    background-color: transparent;\n"
        "    border: 0px;\n"
        "    border-radius: 0px;\n"
        "    top: {runtime_tab_pane_top_offset}px;\n"
        "}}"
    ) in overrides
    assert (
        'QFrame#RuntimeFolder[folderType="tabs"] {{\n'
        "    background-color: {folder_card_bg};\n"
        "    border: {tab_border_width}px solid {separator};\n"
        "    border-radius: {panel_radius}px;\n"
        "    border-top-left-radius: 0px;\n"
        "}}"
    ) in overrides

    # The selected runtime tab carries no second negative offset.
    assert "QWidget#ToolboxContent QTabBar::tab:selected {{" in overrides
    assert "margin-bottom: {runtime_tab_selected_overlap}px;" in overrides

    # Keep the editor Items/Presets pane independent so the runtime host fix
    # does not silently redesign unrelated editor tabs.
    assert "QTabWidget#CreatePaletteTabs::pane {{" in overrides
    assert "QTabWidget#CreatePaletteTabs QTabBar::tab:selected {{" in overrides
    assert "margin-bottom: -{tab_border_width}px;" in overrides
    assert (
        "QWidget#ToolboxContent QTabWidget::pane,\n"
        "QTabWidget#CreatePaletteTabs::pane"
    ) not in overrides
