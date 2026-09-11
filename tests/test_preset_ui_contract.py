# -*- coding: utf-8 -*-

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_create_palette_uses_runtime_folder_tab_style_for_items_and_presets():
    source = _read(
        "scripts/script_toolbox/ui/preset_hooks.py"
    )
    runtime_style = _read(
        "scripts/script_toolbox/style/runtime_overrides.py"
    )

    assert "QtGui.QTabWidget(" in source
    assert '"CreatePaletteTabs"' in source
    assert '"Items"' in source
    assert '"Presets"' in source
    assert "self.palette_scroll_frame" not in source
    assert '"palette_scroll_frame"' in source
    assert "self.palette_filter.setPlaceholderText(" in source

    assert "QWidget#ToolboxContent QTabWidget::pane," in runtime_style
    assert "QTabWidget#CreatePaletteTabs::pane" in runtime_style
    assert "QWidget#ToolboxContent QTabBar::tab," in runtime_style
    assert "QTabWidget#CreatePaletteTabs QTabBar::tab" in runtime_style
    assert "QWidget#ToolboxContent QTabBar::tab:selected," in runtime_style
    assert "QTabWidget#CreatePaletteTabs QTabBar::tab:selected" in runtime_style
    assert "RUNTIME_TAB_SELECTED_OVERLAP" in runtime_style
    assert "font-weight: bold" not in runtime_style
    assert "font-weight: normal" in runtime_style
    assert "palette_tabs.setStyleSheet" not in source


def test_presets_keep_search_below_tabs_and_reuse_scroll_surface_contract():
    source = _read(
        "scripts/script_toolbox/ui/preset_hooks.py"
    )
    base_source = _read(
        "scripts/script_toolbox/ui/interface_editor.py"
    )

    assert "left_layout.insertWidget(" in source
    assert "self.palette_tabs" in source
    assert "wrap_scroll_widget(" in source
    assert "self.preset_scroll_frame" in source

    palette_pos = base_source.index(
        "left_layout.addWidget(\n            self.palette,"
    )
    search_pos = base_source.index(
        "left_layout.addWidget(\n            self.palette_filter"
    )
    assert palette_pos < search_pos


def test_preset_insertion_goes_through_reference_safe_controller_clone():
    source = _read(
        "scripts/script_toolbox/ui/preset_hooks.py"
    )
    ui_init = _read(
        "scripts/script_toolbox/ui/__init__.py"
    )
    controller = _read(
        "scripts/script_toolbox/core/editor_document.py"
    )

    assert "clone = editor._clone_data(" in source
    assert "editor._used_names()" in source
    assert "build_preset_interface_editor_class(" in ui_init
    assert "def clone_subtree(self, data, used_names=None):" in controller
    assert "rewrite_subtree_references(" in controller
