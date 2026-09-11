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


def test_runtime_registry_registers_icon_and_numeric_renderers():
    source = _source(
        "scripts", "script_toolbox", "ui", "runtime_renderers.py"
    )

    assert '("icon", _render_icon)' in source
    assert "safe_numeric_size" in source
    assert 'item.get("show_slider", False)' in source
    assert "QSlider" in source
    assert "component_labels" in source


def test_debounced_runtime_uses_native_binding_dispatch_only():
    source = _source(
        "scripts", "script_toolbox", "ui", "debounced_main_window.py"
    )

    assert "self._run_on_change(" in source
    assert "run_item_callback" not in source
    assert "_LEGACY_CALLBACK_EVENTS" not in source
    assert '"on_change"' not in source


def test_property_editor_uses_compact_trigger_tabs_and_toolbar_language():
    base_source = _source(
        "scripts", "script_toolbox", "ui", "properties", "base.py"
    )
    binding_source = _source(
        "scripts", "script_toolbox", "ui", "properties", "bindings.py"
    )
    language_source = _source(
        "scripts", "script_toolbox", "ui", "language_script_editor.py"
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
    assert "LanguageScriptEditor" in binding_source
    assert "language_combo" in language_source
    assert "callback_tabs" not in base_source


def test_button_editor_is_action_only():
    source = _source(
        "scripts", "script_toolbox", "ui", "properties", "button.py"
    )

    assert "self.language =" not in source
    assert "click_editor" not in source
    assert "shift_editor" not in source
    assert "state_on_language" not in source
    assert "state_off_language" not in source
    assert "state_on_label" not in source
    assert "self.mode" not in source


def test_event_binding_runtime_installs_mouse_filter_and_double_click_delay():
    source = _source(
        "scripts", "script_toolbox", "ui", "event_binding_hooks.py"
    )

    assert "MouseBindingFilter" in source
    assert "MouseButtonDblClick" in source
    assert "doubleClickInterval" in source
    assert '"ctrl"' in source
    assert '"alt"' in source
    assert '"shift"' in source
    assert "dispatch_item_event" in source


def test_icon_property_editor_and_palette_are_registered():
    registry = _source(
        "scripts", "script_toolbox", "ui", "properties", "registry.py"
    )
    bootstrap = _source(
        "scripts", "script_toolbox", "ui", "bootstrap.py"
    )

    assert '"icon": IconPropertyEditor' in registry
    assert '"toggle_icon": ToggleIconPropertyEditor' in registry
    assert '"Icon",' in bootstrap
    assert '"Toggle Icon",' in bootstrap


def test_layout_bindings_are_not_public_runtime_events():
    binding_source = _source(
        "scripts", "script_toolbox", "model", "bindings.py"
    )
    package_source = _source(
        "scripts", "script_toolbox", "ui", "__init__.py"
    )
    bootstrap = _source(
        "scripts", "script_toolbox", "ui", "bootstrap.py"
    )

    assert '"folder": (),' in binding_source
    assert '"row": (),' in binding_source
    assert '"column": (),' in binding_source
    assert '"separator": (),' in binding_source
    assert "controls_v2_hooks" not in package_source
    assert "controls_v2_hooks" not in bootstrap


def test_no_specialized_composition_kinds_were_added():
    source = _source(
        "scripts", "script_toolbox", "constants.py"
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
