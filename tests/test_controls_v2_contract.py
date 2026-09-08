# -*- coding: utf-8 -*-

import os


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


def _source(*parts):
    path = os.path.join(ROOT, *parts)
    return open(path, "r").read()


def test_runtime_registry_registers_icon_and_numeric_v2_renderer():
    source = _source(
        "scripts",
        "script_toolbox",
        "ui",
        "runtime_renderers.py"
    )

    assert '("icon", _render_icon)' in source
    assert "safe_numeric_size" in source
    assert 'item.get("show_slider", False)' in source
    assert "QSlider" in source
    assert "component_labels" in source


def test_active_runtime_routes_value_changes_to_event_bindings():
    source = _source(
        "scripts",
        "script_toolbox",
        "ui",
        "debounced_main_window.py"
    )

    assert '"value_changed"' in source
    assert "dispatch_binding_event" in source
    assert "run_item_callback" in source
    assert '"on_change": "value_changed"' in source


def test_property_editor_uses_compact_trigger_tabs_and_toolbar_language():
    base_source = _source(
        "scripts",
        "script_toolbox",
        "ui",
        "properties",
        "base.py"
    )
    binding_source = _source(
        "scripts",
        "script_toolbox",
        "ui",
        "properties",
        "bindings.py"
    )
    language_source = _source(
        "scripts",
        "script_toolbox",
        "ui",
        "language_script_editor.py"
    )

    assert "BindingPanel" in base_source
    assert '"Triggers"' in binding_source
    assert "setCornerWidget" in binding_source
    assert "QToolButton(self.tabs)" in binding_source
    assert 'setText("+")' in binding_source
    assert "setTabsClosable(True)" in binding_source
    assert "tabCloseRequested" in binding_source
    assert "MouseButtonDblClick" in binding_source
    assert "Double-click to edit trigger" in binding_source
    assert "QMessageBox.question" in binding_source
    assert "edit_button =" not in binding_source
    assert "remove_button =" not in binding_source
    assert "LanguageScriptEditor" in binding_source
    assert "toolbar_layout.addWidget" in language_source
    assert "language_combo" in language_source
    assert 'QLabel("Language")' not in language_source
    assert "callback_tabs" not in base_source


def test_button_editor_has_no_global_language_or_click_shift_tabs():
    source = _source(
        "scripts",
        "script_toolbox",
        "ui",
        "properties",
        "button.py"
    )

    assert "self.language =" not in source
    assert "click_editor" not in source
    assert "shift_editor" not in source
    assert 'item.pop("language", None)' in source
    assert 'item.pop("click_script", None)' in source
    assert 'item.pop("shift_script", None)' in source
    assert "state_on_language" in source
    assert "state_off_language" in source


def test_event_binding_runtime_installs_mouse_filter_and_double_click_delay():
    source = _source(
        "scripts",
        "script_toolbox",
        "ui",
        "event_binding_hooks.py"
    )

    assert "MouseBindingFilter" in source
    assert "MouseButtonDblClick" in source
    assert "doubleClickInterval" in source
    assert '"ctrl"' in source
    assert '"alt"' in source
    assert '"shift"' in source
    assert "dispatch_item_event" in source


def test_icon_property_editor_and_palette_are_installed():
    registry = _source(
        "scripts",
        "script_toolbox",
        "ui",
        "properties",
        "registry.py"
    )
    ui_init = _source(
        "scripts",
        "script_toolbox",
        "ui",
        "__init__.py"
    )

    assert '"icon": IconPropertyEditor' in registry
    assert '"Icon",' in ui_init
    assert '"icon",' in ui_init
    assert "event bindings" in ui_init


def test_layout_trigger_ui_is_disabled_but_folder_compatibility_hook_remains():
    binding_source = _source(
        "scripts",
        "script_toolbox",
        "model",
        "bindings.py"
    )
    hook_source = _source(
        "scripts",
        "script_toolbox",
        "ui",
        "controls_v2_hooks.py"
    )

    assert '"folder": (),' in binding_source
    assert '"row": (),' in binding_source
    assert '"separator": (),' in binding_source
    assert '"folder": ("opened", "closed")' in binding_source
    assert '"on_open"' in hook_source
    assert '"on_close"' in hook_source


def test_no_specialized_composition_kinds_were_added():
    source = _source(
        "scripts",
        "script_toolbox",
        "constants.py"
    )

    for forbidden in (
        '"selection_set"',
        '"node_picker"',
        '"file_picker"',
        '"folder_picker"',
        '"button_group"',
        '"slider"',
        '"vector2"',
        '"vector3"',
        '"vector4"',
    ):
        assert forbidden not in source
