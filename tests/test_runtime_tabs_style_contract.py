# -*- coding: utf-8 -*-

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_runtime_tabs_own_one_seam_compensation():
    metrics = _read("scripts/script_toolbox/style/metrics.py")
    overrides = _read("scripts/script_toolbox/style/runtime_overrides.py")

    # Runtime and editor panes deliberately have separate vertical contracts.
    # Runtime keeps the pane at its native origin; the selected tab owns the
    # only one-pixel overlap. This prevents a pane shift plus tab shift from
    # clipping rounded borders differently across Qt4/Qt5 hosts.
    assert "TAB_PANE_TOP_OFFSET = -1" in metrics
    assert "RUNTIME_TAB_PANE_TOP_OFFSET = 0" in metrics
    assert "RUNTIME_TAB_SELECTED_OVERLAP = -1" in metrics
    assert "RUNTIME_TAB_PANE_TOP_OFFSET" in overrides
    assert "top: {runtime_tab_pane_top_offset}px;" in overrides
    assert "top: {tab_pane_top_offset}px;" in overrides

    # Runtime pane geometry is scoped to ToolboxContent and the tab bar owns
    # the top-left visual corner, so the pane must not add a second rounded
    # corner underneath the first tab.
    assert "QWidget#ToolboxContent QTabWidget::pane {{" in overrides
    assert "border-radius: {panel_radius}px;" in overrides
    assert "border-top-left-radius: 0px;" in overrides

    # Keep the editor Items/Presets pane independent so a runtime host fix does
    # not silently redesign unrelated editor tabs.
    assert "QTabWidget#CreatePaletteTabs::pane {{" in overrides
    assert (
        "QWidget#ToolboxContent QTabWidget::pane,\n"
        "QTabWidget#CreatePaletteTabs::pane"
    ) not in overrides
