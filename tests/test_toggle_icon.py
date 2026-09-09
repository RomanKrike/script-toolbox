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
            "label": "Wireframe",
            "state_on_path": "on.svg",
            "state_off_path": "off.svg",
            "value": True,
        }
    )

    assert item["kind"] == "toggle_icon"
    assert item["state_source"] == "internal"
    assert item["value"] is True
    assert item["state_on_path"] == "on.svg"
    assert item["state_off_path"] == "off.svg"
    assert item["show_label"] is False

    triggers = matching_bindings(
        item,
        "click",
        mouse_button="left",
        modifiers=[]
    )
    assert len(triggers) == 1
    assert triggers[0]["handler"] == "state_toggle"


def test_toggle_icon_script_state_has_no_stored_value():
    item = create_item(
        "toggle_icon",
        {
            "state_source": "script",
            "value": True,
            "state_get_script": "state = True",
            "state_on_script": "print('on')",
            "state_off_script": "print('off')",
        }
    )

    assert item["state_source"] == "script"
    assert "value" not in item
    assert item["state_get_script"] == "state = True"
    assert item["state_on_script"] == "print('on')"
    assert item["state_off_script"] == "print('off')"


def test_toggle_icon_can_use_legacy_icon_path_as_both_state_fallbacks():
    item = create_item(
        "toggle_icon",
        {
            "path": "shared.svg",
        }
    )

    assert item["state_on_path"] == "shared.svg"
    assert item["state_off_path"] == "shared.svg"
    assert "path" not in item


def test_toggle_icon_editor_and_runtime_are_registered():
    ui_source = _source(
        "scripts",
        "script_toolbox",
        "ui",
        "__init__.py"
    )
    registry_source = _source(
        "scripts",
        "script_toolbox",
        "ui",
        "properties",
        "registry.py"
    )
    runtime_source = _source(
        "scripts",
        "script_toolbox",
        "ui",
        "toggle_icon_runtime.py"
    )

    assert '"Toggle Icon"' in ui_source
    assert '"toggle_icon"' in ui_source
    assert "render_toggle_icon" in ui_source
    assert '"toggle_icon": ToggleIconPropertyEditor' in registry_source
    assert "state_on_path" in runtime_source
    assert "state_off_path" in runtime_source
    assert "run_state_binding" in runtime_source
