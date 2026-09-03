# -*- coding: utf-8 -*-

from script_toolbox.core.values import find_item
from script_toolbox.core.values import get_value
from script_toolbox.core.values import normalize_value
from script_toolbox.core.values import store_value
from script_toolbox.model.items import normalize_document


def sample_document():
    return normalize_document({
        "sections": [
            {
                "name": "root",
                "items": [
                    {
                        "kind": "integer",
                        "name": "count",
                        "min": 0,
                        "max": 10,
                        "value": 3,
                    },
                    {
                        "kind": "float",
                        "name": "amount",
                        "min": -1.0,
                        "max": 1.0,
                        "value": 0.25,
                    },
                    {
                        "kind": "checkbox",
                        "name": "enabled",
                        "value": False,
                    },
                    {
                        "kind": "menu",
                        "name": "mode",
                        "items": ["A", "B"],
                        "value": "A",
                    },
                    {
                        "kind": "color",
                        "name": "tint",
                        "value": [0.1, 0.2, 0.3],
                    },
                    {
                        "kind": "field",
                        "name": "selection",
                        "value": "",
                    },
                ],
            }
        ]
    })


def test_find_item_by_id_name_and_label():
    document = sample_document()
    item = find_item(document, "count")

    assert item is not None
    assert find_item(document, item["id"]) is item
    assert find_item(document, item["label"]) is item


def test_get_value_returns_default_for_missing_item():
    document = sample_document()

    assert get_value(
        document,
        "missing",
        default="fallback"
    ) == "fallback"


def test_integer_and_float_values_are_clamped():
    document = sample_document()

    assert store_value(
        document,
        "count",
        99
    )["value"] == 10

    assert store_value(
        document,
        "amount",
        -99.0
    )["value"] == -1.0


def test_menu_rejects_unknown_value():
    document = sample_document()
    item = find_item(
        document,
        "mode"
    )

    assert normalize_value(
        item,
        "unknown"
    ) == "A"


def test_color_is_normalized_to_zero_one_range():
    document = sample_document()

    result = store_value(
        document,
        "tint",
        [-1.0, 0.5, 5.0]
    )

    assert result["value"] == [
        0.0,
        0.5,
        1.0,
    ]


def test_field_accepts_list_values_as_text():
    document = sample_document()

    result = store_value(
        document,
        "selection",
        ["|group|meshA", "meshB"]
    )

    assert result["value"] == [
        "|group|meshA",
        "meshB",
    ]


def test_store_value_returns_none_for_non_value_item():
    document = normalize_document({
        "sections": [
            {
                "name": "root",
                "items": [
                    {
                        "kind": "button",
                        "name": "run",
                    }
                ],
            }
        ]
    })

    assert store_value(
        document,
        "run",
        123
    ) is None
