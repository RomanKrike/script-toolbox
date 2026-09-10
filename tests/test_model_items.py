# -*- coding: utf-8 -*-

import pytest

from script_toolbox.constants import CONFIG_VERSION
from script_toolbox.model.items import create_item
from script_toolbox.model.items import normalize_document
from script_toolbox.model.items import safe_color
from script_toolbox.model.items import safe_menu_items
from script_toolbox.model.items import sanitize_name


def test_sanitize_name_handles_spaces_symbols_and_leading_digits():
    assert sanitize_name(
        "  123 Render Samples!  "
    ) == "_123_Render_Samples"


def test_safe_menu_items_accepts_list_and_text():
    assert safe_menu_items(["A", "", "B"]) == ["A", "B"]
    assert safe_menu_items("A, B\nC") == ["A", "B", "C"]


def test_safe_color_uses_default_and_clamps_values():
    assert safe_color(None) == [0.25, 0.25, 0.25]
    assert safe_color([-1, 0.5, 2]) == [0.0, 0.5, 1.0]


def test_integer_swaps_invalid_min_max_and_clamps_value():
    item = create_item(
        "integer",
        {
            "min": 10,
            "max": 1,
            "value": 99,
            "step": 0,
        }
    )

    assert item["min"] == 1
    assert item["max"] == 10
    assert item["value"] == 10
    assert item["step"] == 1


def test_float_normalizes_decimals_and_step():
    item = create_item(
        "float",
        {
            "min": 5.0,
            "max": -5.0,
            "value": 100.0,
            "step": 0,
            "decimals": 99,
        }
    )

    assert item["min"] == -5.0
    assert item["max"] == 5.0
    assert item["value"] == 5.0
    assert item["step"] > 0
    assert item["decimals"] == 8


def test_button_is_action_only():
    item = create_item(
        "button",
        {
            "label": "Freeze",
            "mode": "state",
            "state_get_script": "state = True",
        }
    )

    assert item["kind"] == "button"
    assert "mode" not in item
    assert "state_get_script" not in item
    assert len(item["bindings"]) == 1
    assert item["bindings"][0]["handler"] == "script"
    assert "button_mode" not in item["bindings"][0]


def test_toggle_button_defaults_to_internal_boolean_state():
    item = create_item(
        "toggle_button",
        {
            "label": "Wireframe",
        }
    )

    assert item["kind"] == "toggle_button"
    assert item["state_source"] == "internal"
    assert item["value"] is False
    assert item["state_on_label"] == "Wireframe"
    assert item["state_off_label"] == "Wireframe"
    assert len(item["bindings"]) == 1
    assert item["bindings"][0]["handler"] == "state_toggle"
    assert "button_mode" not in item["bindings"][0]


def test_toggle_button_preserves_script_state_configuration():
    item = create_item(
        "toggle_button",
        {
            "state_source": "script",
            "state_get_script": "state = cmds.grid(q=True, toggle=True)",
            "state_on_script": "cmds.grid(toggle=True)",
            "state_off_script": "cmds.grid(toggle=False)",
            "state_on_language": "python",
            "state_off_language": "python",
        }
    )

    assert item["state_source"] == "script"
    assert "value" not in item
    assert item["state_get_language"] == "python"
    assert item["state_get_script"].startswith("state =")
    assert item["state_on_script"]
    assert item["state_off_script"]


def test_unknown_kind_is_rejected():
    with pytest.raises(ValueError):
        create_item(
            "does_not_exist",
            {"name": "unsupported"}
        )


def test_invalid_document_falls_back_to_new_current_document():
    document = normalize_document(None)

    assert document["version"] == CONFIG_VERSION
    assert len(document["sections"]) == 1
    assert document["sections"][0]["kind"] == "folder"


def test_old_folders_root_is_not_interpreted():
    document = normalize_document({
        "folders": [
            {
                "name": "old_root",
                "label": "Old Root",
            }
        ]
    })

    assert document["version"] == CONFIG_VERSION
    assert document["sections"][0]["name"] == "my_tools"
    assert document["sections"][0]["name"] != "old_root"
