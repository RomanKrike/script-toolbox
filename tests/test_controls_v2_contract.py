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


def test_active_runtime_callback_namespace_uses_execution_result():
    source = _source(
        "scripts",
        "script_toolbox",
        "ui",
        "debounced_main_window.py"
    )

    assert "execute_script_result" in source
    assert '"toolbox": self' in source
    assert '"item": item' in source
    assert '"value": value' in source
    assert '"old_value": old_value' in source
    assert '"event": event' in source
    assert 'context="callback:{0}:{1}"' in source


def test_property_editor_uses_shared_callback_tabs():
    source = _source(
        "scripts",
        "script_toolbox",
        "ui",
        "properties",
        "base.py"
    )

    assert 'QGroupBox("Callbacks (Python)")' in source
    assert "callback_events" in source
    assert "callback_script" in source
    assert 'item["callbacks"] = callbacks' in source


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


def test_controls_v2_runtime_hooks_keep_state_icon_only_and_folder_events():
    source = _source(
        "scripts",
        "script_toolbox",
        "ui",
        "controls_v2_hooks.py"
    )

    assert 'item.get("icon_only", False)' in source
    assert 'widget.setText("")' in source
    assert '"on_open"' in source
    assert '"on_close"' in source
    assert "RuntimeFolderTabs" in source
    assert "RuntimeFolderRadio" in source


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
