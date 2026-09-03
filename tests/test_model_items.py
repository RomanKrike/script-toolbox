# -*- coding: utf-8 -*-

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
    assert safe_menu_items(
        ["A", "", "B"]
    ) == [
        "A",
        "B",
    ]

    assert safe_menu_items(
        "A, B\nC"
    ) == [
        "A",
        "B",
        "C",
    ]


def test_safe_color_uses_default_and_clamps_values():
    assert safe_color(
        None
    ) == [
        0.25,
        0.25,
        0.25,
    ]

    assert safe_color(
        [-1, 0.5, 2]
    ) == [
        0.0,
        0.5,
        1.0,
    ]


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


def test_unknown_kind_falls_back_to_button():
    item = create_item(
        "does_not_exist",
        {
            "name": "fallback",
        }
    )

    assert item["kind"] == "button"
    assert item["name"] == "fallback"


def test_invalid_document_falls_back_to_default_root_folder():
    document = normalize_document(
        None
    )

    assert document["version"] == CONFIG_VERSION
    assert len(document["sections"]) == 1
    assert document["sections"][0]["kind"] == "folder"


def test_old_folders_key_is_supported():
    document = normalize_document({
        "folders": [
            {
                "name": "legacy",
                "label": "Legacy",
            }
        ]
    })

    assert document["sections"][0]["name"] == "legacy"
