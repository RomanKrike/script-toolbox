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


def test_runtime_registry_registers_icon_and_numeric_renderers_from_metadata():
    source = _source(
        "scripts", "script_toolbox", "ui", "runtime_renderers.py"
    )
    definitions = _source(
        "scripts", "script_toolbox", "model", "item_builtins.py"
    )

    assert 'renderer_path=".runtime_renderers:_render_icon"' in definitions
    assert 'renderer_path=".runtime_renderers:_render_integer"' in definitions
    assert 'renderer_path=".runtime_renderers:_render_float"' in definitions
    assert "for definition in ITEM_TYPES.all():" in source
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
    assert "class BindingPanel(QtGui.QWidget):" in binding_source
    assert "class TriggerTabWidget(QtGui.QTabWidget):" in binding_source
    assert "setCornerWidget" not in binding_source
    assert 'self._add_page.setObjectName("TriggerAddTabPage")' in binding_source
    assert 'self._add_page,\n            "+"' in binding_source
    assert "setTabsClosable(True)" in binding_source
    assert "tabCloseRequested" in binding_source
    assert "MouseButtonPress" in binding_source
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


def test_icon_property_editor_and_palette_are_registry_driven():
    definitions = _source(
        "scripts", "script_toolbox", "model", "item_builtins.py"
    )
    ui_bootstrap = _source(
        "scripts", "script_toolbox", "ui", "item_ui_bootstrap.py"
    )
    palette = _source(
        "scripts", "script_toolbox", "ui", "item_palette.py"
    )

    assert 'inspector_path=".properties.icon:IconPropertyEditor"' in definitions
    assert (
        'inspector_path=".properties.toggle_icon:ToggleIconPropertyEditor"'
        in definitions
    )
    assert '"icon", "Icon", "Display", 10' in definitions
    assert '"toggle_icon", "Toggle Icon", "Controls", 30' in definitions
    assert "for definition in ITEM_TYPES.all():" in ui_bootstrap
    assert "ITEM_TYPES.creatable()" in palette


def test_layout_bindings_are_not_public_runtime_events():
    binding_source = _source(
        "scripts", "script_toolbox", "model", "bindings.py"
    )
    definitions = _source(
        "scripts", "script_toolbox", "model", "item_builtins.py"
    )
    package_source = _source(
        "scripts", "script_toolbox", "ui", "__init__.py"
    )
    bootstrap = _source(
        "scripts", "script_toolbox", "ui", "bootstrap.py"
    )

    assert "definition.events" in binding_source
    assert "EVENT_CAPABILITIES" not in binding_source
    assert '"folder", "Folder", "Layout", 10' in definitions
    assert '"row", "Row", "Layout", 20' in definitions
    assert '"column", "Column", "Layout", 30' in definitions
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
