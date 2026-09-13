# -*- coding: utf-8 -*-

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_toggle_state_pages_share_binding_panel_tab_widget():
    for relative_path in (
        "scripts/script_toolbox/ui/properties/toggle_button.py",
        "scripts/script_toolbox/ui/properties/toggle_icon.py",
    ):
        source = _read(relative_path)

        assert "from .inspector_tabs import add_inspector_script_tab" in source
        assert "self.state_tabs = QtGui.QTabWidget()" not in source
        assert "style_inspector_tabs(self.state_tabs)" not in source
        assert "self.add_trigger_widget(self.state_tabs" not in source

        assert "tabs = self.binding_panel.tabs" in source
        assert "def _detach_state_tabs(" in source
        assert "def _sync_state_tabs(" in source
        assert "page = add_inspector_script_tab(" in source
        assert "tabs.setTabEnabled(index, True)" in source
        assert "tabs.tabBar().setTabEnabled(index, True)" in source
        assert "self.state_get_editor.setEnabled(True)" in source


def test_toggle_bind_detaches_fixed_pages_before_binding_panel_rebuild():
    button_source = _read(
        "scripts/script_toolbox/ui/properties/toggle_button.py"
    )
    icon_source = _read(
        "scripts/script_toolbox/ui/properties/toggle_icon.py"
    )

    assert "self._detach_state_tabs()\n        ButtonPropertyEditor.bind(self, item)" in button_source
    assert "self._detach_state_tabs()\n        PropertyEditorBase.bind(self, item)" in icon_source


def test_toggle_state_pages_are_reappended_after_event_binding_pages():
    for relative_path in (
        "scripts/script_toolbox/ui/properties/toggle_button.py",
        "scripts/script_toolbox/ui/properties/toggle_icon.py",
    ):
        source = _read(relative_path)
        assert "self.binding_panel.changed.connect(self._sync_state_tabs)" in source
        assert "self._detach_state_tabs()" in source
        assert "tabs.addTab(page, label)" in source
        assert "self._hide_state_tab_close_button(index)" in source


def test_add_trigger_button_stays_right_of_event_tabs_before_fixed_state_tabs():
    binding_source = _read(
        "scripts/script_toolbox/ui/properties/bindings.py"
    )
    assert "self.tabs.setCornerWidget(" in binding_source
    assert "QtCore.Qt.TopRightCorner" in binding_source

    for relative_path in (
        "scripts/script_toolbox/ui/properties/toggle_button.py",
        "scripts/script_toolbox/ui/properties/toggle_icon.py",
    ):
        source = _read(relative_path)
        assert "tabs.addTab(page, label)" in source


def test_state_script_tabs_use_same_page_geometry_as_event_binding_pages():
    tab_source = _read(
        "scripts/script_toolbox/ui/properties/inspector_tabs.py"
    )
    binding_source = _read(
        "scripts/script_toolbox/ui/properties/bindings.py"
    )

    for expected in (
        "TRIGGER_PAGE_MARGINS",
        "TRIGGER_PAGE_SPACING",
    ):
        assert expected in tab_source
        assert expected in binding_source

    assert "def add_inspector_script_tab(" in tab_source
    assert "margins=TRIGGER_PAGE_MARGINS" in tab_source
    assert "spacing=TRIGGER_PAGE_SPACING" in tab_source
    assert "margins=TRIGGER_PAGE_MARGINS" in binding_source
    assert "spacing=TRIGGER_PAGE_SPACING" in binding_source


def test_trigger_panel_has_no_redundant_events_group_box_chrome():
    binding_source = _read(
        "scripts/script_toolbox/ui/properties/bindings.py"
    )
    tab_source = _read(
        "scripts/script_toolbox/ui/properties/inspector_tabs.py"
    )

    assert "from .inspector_tabs import style_binding_panel" in binding_source
    assert "from .inspector_tabs import style_inspector_tabs" in binding_source
    assert 'QtGui.QGroupBox.__init__(self, "", parent)' in binding_source
    assert "style_binding_panel(self)" in binding_source
    assert "style_inspector_tabs(self.tabs)" in binding_source
    assert 'QtGui.QGroupBox.setTitle(self, "")' in binding_source

    assert "QGroupBox#TriggerBindingPanel" in tab_source
    assert "background-color: transparent" in tab_source
    assert "margin: 0px" in tab_source
    assert "padding: 0px" in tab_source
    assert "panel.setContentsMargins(0, 0, 0, 0)" in tab_source


def test_inspector_tabs_reuse_runtime_tab_palette_and_metrics_without_nested_pane():
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
    assert "background-color: transparent" in source
    assert "border: 0px" in source
    assert "border-radius: 0px" in source
    assert "QTabWidget#InspectorTabs QTabBar::tab:selected" in source
