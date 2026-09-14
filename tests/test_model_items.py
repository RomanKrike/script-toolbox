# -*- coding: utf-8 -*-

import pytest

from script_toolbox.constants import CONFIG_VERSION
from script_toolbox.model.items import create_item
from script_toolbox.model.items import normalize_document
from script_toolbox.model.items import safe_color
from script_toolbox.model.items import safe_menu_items
from script_toolbox.model.items import sanitize_name


def test_sanitize_name_handles_spaces_symbols_and_leading_digits():
    assert sanitize_name("  123 Render Samples!  ") == "_123_Render_Samples"


def test_safe_menu_items_accepts_list_and_text():
    assert safe_menu_items(["A", "", "B"]) == ["A", "B"]
    assert safe_menu_items("A, B\nC") == ["A", "B", "C"]


def test_safe_color_uses_default_and_clamps_values():
    assert safe_color(None) == [0.25, 0.25, 0.25]
    assert safe_color([-1, 0.5, 2]) == [0.0, 0.5, 1.0]


def test_integer_swaps_invalid_min_max_and_clamps_value():
    item = create_item(
        "integer",
        {"props": {"min": 10, "max": 1, "value": 99, "step": 0}}
    )
    assert item["props"]["min"] == 1
    assert item["props"]["max"] == 10
    assert item["props"]["value"] == 10
    assert item["props"]["step"] == 1


def test_float_normalizes_decimals_and_step():
    item = create_item(
        "float",
        {"props": {"min": 5.0, "max": -5.0, "value": 100.0, "step": 0, "decimals": 99}}
    )
    assert item["props"]["min"] == -5.0
    assert item["props"]["max"] == 5.0
    assert item["props"]["value"] == 5.0
    assert item["props"]["step"] > 0
    assert item["props"]["decimals"] == 8


def test_button_is_action_only_and_legacy_root_props_are_ignored():
    item = create_item(
        "button",
        {"ui": {"label": "Freeze"}, "mode": "state", "state_get_script": "state = True"}
    )
    assert item["kind"] == "button"
    assert "mode" not in item["props"]
    assert "state_get_script" not in item["props"]
    assert item["bindings"][0]["handler"] == "script"


def test_toggle_button_defaults_to_internal_boolean_state():
    item = create_item("toggle_button", {"ui": {"label": "Wireframe"}})
    assert item["props"]["state_source"] == "internal"
    assert item["props"]["value"] is False
    assert item["props"]["state_on_label"] == "Wireframe"
    assert item["props"]["state_off_label"] == "Wireframe"
    assert item["bindings"][0]["handler"] == "state_toggle"


def test_toggle_button_preserves_script_state_configuration():
    item = create_item(
        "toggle_button",
        {
            "props": {
                "state_source": "script",
                "state_get_script": "state = cmds.grid(q=True, toggle=True)",
                "state_on_script": "cmds.grid(toggle=True)",
                "state_off_script": "cmds.grid(toggle=False)",
                "state_on_language": "python",
                "state_off_language": "python",
            },
        }
    )
    assert item["props"]["state_source"] == "script"
    assert "value" not in item["props"]
    assert item["props"]["state_get_language"] == "python"
    assert item["props"]["state_get_script"].startswith("state =")


def test_unknown_kind_is_rejected():
    with pytest.raises(ValueError):
        create_item("does_not_exist", {"name": "unsupported"})


def test_invalid_document_falls_back_to_new_current_document():
    document = normalize_document(None)
    assert document["version"] == CONFIG_VERSION
    assert document["sections"][0]["kind"] == "folder"


def test_old_folders_root_is_not_interpreted():
    document = normalize_document({"folders": [{"name": "old_root"}]})
    assert document["version"] == CONFIG_VERSION
    assert document["sections"][0]["name"] == "my_tools"
