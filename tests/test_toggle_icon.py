# -*- coding: utf-8 -*-

import os

from script_toolbox.model.bindings import matching_bindings
from script_toolbox.model.items import create_item


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


def _source(*parts):
    path = os.path.join(ROOT, *parts)
    return open(path, "r").read()


def test_toggle_icon_internal_state_is_a_boolean_value_item():
    item = create_item(
        "toggle_icon",
        {
            "ui": {"label": "Wireframe"},
            "props": {
                "state_on_path": "on.svg",
                "state_off_path": "off.svg",
                "content_alignment": "center",
                "value": True,
            },
        }
    )

    props = item["props"]
    assert item["kind"] == "toggle_icon"
    assert props["state_source"] == "internal"
    assert props["value"] is True
    assert props["state_on_path"] == "on.svg"
    assert props["state_off_path"] == "off.svg"
    assert props["content_alignment"] == "center"
    assert item["ui"]["show_label"] is False

    triggers = matching_bindings(
        item,
        "click",
        mouse_button="left",
        modifiers=[]
    )
    assert len(triggers) == 1
    assert triggers[0]["handler"] == "state_toggle"
    assert "button_mode" not in triggers[0]


def test_toggle_icon_script_state_has_no_stored_value():
    item = create_item(
        "toggle_icon",
        {
            "props": {
                "state_source": "script",
                "value": True,
                "state_get_script": "state = True",
                "state_on_script": "print('on')",
                "state_off_script": "print('off')",
            },
        }
    )

    props = item["props"]
    assert props["state_source"] == "script"
    assert "value" not in props
    assert props["state_get_script"] == "state = True"
    assert props["state_on_script"] == "print('on')"
    assert props["state_off_script"] == "print('off')"


def test_toggle_icon_does_not_translate_plain_icon_path():
    item = create_item(
        "toggle_icon",
        {
            "props": {"path": "shared.svg"},
        }
    )

    assert item["props"]["state_on_path"] == ""
    assert item["props"]["state_off_path"] == ""
    assert "path" not in item["props"]


def test_toggle_icon_editor_renderer_and_state_runtime_are_registered():
    definitions = _source(
        "scripts", "script_toolbox", "model", "item_builtins.py"
    )
    ui_bootstrap = _source(
        "scripts", "script_toolbox", "ui", "item_ui_bootstrap.py"
    )
    renderer_source = _source(
        "scripts", "script_toolbox", "ui", "toggle_icon_runtime.py"
    )
    main_source = _source(
        "scripts", "script_toolbox", "ui", "main_window.py"
    )

    assert (
        'inspector_path=".properties.toggle_icon:ToggleIconPropertyEditor"'
        in definitions
    )
    assert (
        'renderer_path=".toggle_icon_runtime:render_toggle_icon"'
        in definitions
    )
    assert "_resolve_ui_target" in ui_bootstrap
    assert "register_toggle_icon" in renderer_source
    assert "refresh_toggle_icon" in renderer_source
    assert "state_on_path" in main_source
    assert "state_off_path" in main_source
    assert "def run_state_binding(" in main_source
