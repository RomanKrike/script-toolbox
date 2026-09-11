# -*- coding: utf-8 -*-

import os


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _source(*parts):
    path = os.path.join(ROOT, *parts)
    with open(path, "r") as handle:
        return handle.read()


def test_toggle_state_scripts_share_the_event_tab_surface():
    source = _source(
        "scripts",
        "script_toolbox",
        "ui",
        "properties",
        "toggle_state_tabs.py"
    )

    assert "def install_integrated_toggle_state_tabs():" in source
    assert "def add_auxiliary_tab(" in source
    assert "def set_auxiliary_tab_enabled(" in source
    assert "def script_editor_widgets(" in source
    assert '"state_get"' in source
    assert '"state_on"' in source
    assert '"state_off"' in source
    assert '"Get State"' in source
    assert '"Turn ON"' in source
    assert '"Turn OFF"' in source
    assert "editor.trigger_section.content_layout.removeWidget(state_tabs)" in source
    assert "panel_class.clear = clear" in source
    assert "panel_class._add_page = add_page" in source
    assert "panel_class.eventFilter = event_filter" in source
    assert "self.tabs.indexOf(" in source
    assert "self._add_tab_page" in source


def test_toggle_state_tab_hook_installs_after_trigger_and_sizing_hooks():
    source = _source(
        "scripts",
        "script_toolbox",
        "ui",
        "properties",
        "__init__.py"
    )

    trigger_pos = source.index("install_integrated_trigger_tabs()")
    sizing_pos = source.index("install_expanding_script_editors()")
    state_pos = source.index("install_integrated_toggle_state_tabs()")

    assert trigger_pos < sizing_pos < state_pos
    assert (
        "from .toggle_state_tabs import install_integrated_toggle_state_tabs"
        in source
    )


def test_toggle_state_persistence_contract_is_unchanged():
    toggle_button = _source(
        "scripts",
        "script_toolbox",
        "ui",
        "properties",
        "toggle_button.py"
    )
    toggle_icon = _source(
        "scripts",
        "script_toolbox",
        "ui",
        "properties",
        "toggle_icon.py"
    )

    for source in (toggle_button, toggle_icon):
        assert 'item["state_get_script"]' in source
        assert 'item["state_on_script"]' in source
        assert 'item["state_off_script"]' in source
        assert 'item["state_get_language"] = "python"' in source
