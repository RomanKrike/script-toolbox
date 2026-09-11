# -*- coding: utf-8 -*-

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_runtime_tabs_use_one_bar_owned_seam_compensation():
    metrics = _read("scripts/script_toolbox/style/metrics.py")
    overrides = _read("scripts/script_toolbox/style/runtime_overrides.py")

    # Runtime and editor panes deliberately have separate vertical contracts.
    # Runtime keeps the pane and selected tab at their natural positions; the
    # tab bar alone moves down by one border width to cover the pane seam.
    assert "TAB_PANE_TOP_OFFSET = -1" in metrics
    assert "RUNTIME_TAB_BAR_VERTICAL_OFFSET = TAB_BORDER_WIDTH" in metrics
    assert "RUNTIME_TAB_PANE_TOP_OFFSET = 0" in metrics
    assert "RUNTIME_TAB_SELECTED_OVERLAP = 0" in metrics
    assert "RUNTIME_TAB_BAR_VERTICAL_OFFSET" in overrides
    assert "top: {runtime_tab_bar_vertical_offset}px;" in overrides
    assert "top: {runtime_tab_pane_top_offset}px;" in overrides
    assert "top: {tab_pane_top_offset}px;" in overrides

    # Runtime pane geometry is scoped to ToolboxContent and the tab bar owns
    # the top-left visual corner, so the pane does not add a second rounded
    # corner underneath the first tab.
    assert "QWidget#ToolboxContent QTabWidget::pane {{" in overrides
    assert "border-radius: {panel_radius}px;" in overrides
    assert "border-top-left-radius: 0px;" in overrides

    # The selected runtime tab no longer carries a second negative offset.
    assert "QWidget#ToolboxContent QTabBar::tab:selected {{" in overrides
    assert "margin-bottom: {runtime_tab_selected_overlap}px;" in overrides

    # Keep the editor Items/Presets pane independent so a runtime host fix does
    # not silently redesign unrelated editor tabs.
    assert "QTabWidget#CreatePaletteTabs::pane {{" in overrides
    assert "QTabWidget#CreatePaletteTabs QTabBar::tab:selected {{" in overrides
    assert "margin-bottom: -{tab_border_width}px;" in overrides
    assert (
        "QWidget#ToolboxContent QTabWidget::pane,\n"
        "QTabWidget#CreatePaletteTabs::pane"
    ) not in overrides
