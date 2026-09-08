# -*- coding: utf-8 -*-

from script_toolbox.core import values as values_module
from script_toolbox.core.values import find_item
from script_toolbox.core.values import get_document_index
from script_toolbox.core.values import get_value
from script_toolbox.core.values import invalidate_document_index
from script_toolbox.core.values import store_value
from script_toolbox.model import DocumentIndex
from script_toolbox.model import index as index_module
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
                        "label": "Count Label",
                        "min": 0,
                        "max": 10,
                        "value": 3,
                    },
                    {
                        "kind": "float",
                        "name": "amount",
                        "label": "Amount Label",
                        "min": -1.0,
                        "max": 1.0,
                        "value": 0.25,
                    },
                ],
            }
        ]
    })


def test_document_index_finds_by_id_name_and_label():
    document = sample_document()
    index = DocumentIndex(document)
    item = document["sections"][0]["items"][0]

    assert index.find(item["id"]) is item
    assert index.find("count") is item
    assert index.find("Count Label") is item
    assert index.find("missing") is None


def test_document_index_preserves_id_name_label_precedence():
    document = sample_document()
    count = document["sections"][0]["items"][0]
    amount = document["sections"][0]["items"][1]

    amount["id"] = "count"
    amount["label"] = "count"

    index = DocumentIndex(document)

    assert index.find("count") is amount
    assert count["name"] == "count"


def test_document_index_preserves_first_item_for_duplicate_field():
    document = sample_document()
    first = document["sections"][0]["items"][0]
    second = document["sections"][0]["items"][1]

    first["label"] = "Shared"
    second["label"] = "Shared"

    index = DocumentIndex(document)

    assert index.find("Shared") is first


def test_value_api_reuses_cached_index_for_successful_lookups(monkeypatch):
    invalidate_document_index()
    document = sample_document()
    item = find_item(document, "count")

    def fail_walk(*args, **kwargs):
        raise AssertionError(
            "stable indexed lookup must not traverse the document again"
        )

    monkeypatch.setattr(
        index_module,
        "walk_items",
        fail_walk
    )
    monkeypatch.setattr(
        values_module,
        "walk_items",
        fail_walk
    )

    assert find_item(document, "count") is item
    assert get_value(document, "count") == 3
    assert store_value(document, "count", 4) is item
    assert get_value(document, "count") == 4


def test_document_replacement_gets_a_new_index():
    invalidate_document_index()
    first_document = sample_document()
    second_document = sample_document()

    first_index = get_document_index(
        first_document
    )
    second_index = get_document_index(
        second_document
    )

    assert first_index is not second_index
    assert first_index.document is first_document
    assert second_index.document is second_document


def test_invalidate_document_index_rebuilds_on_next_access():
    invalidate_document_index()
    document = sample_document()

    first_index = get_document_index(
        document
    )
    invalidate_document_index(
        document
    )
    second_index = get_document_index(
        document
    )

    assert first_index is not second_index


def test_in_place_name_change_self_heals_cached_index():
    invalidate_document_index()
    document = sample_document()
    item = find_item(document, "count")

    item["name"] = "renamed_count"

    assert find_item(document, "renamed_count") is item
    assert find_item(document, "count") is None


def test_in_place_structure_addition_self_heals_cached_index():
    invalidate_document_index()
    document = sample_document()
    assert find_item(document, "count") is not None

    new_item = normalize_document({
        "sections": [
            {
                "name": "temp",
                "items": [
                    {
                        "kind": "integer",
                        "name": "late_item",
                        "min": 0,
                        "max": 10,
                        "value": 5,
                    }
                ],
            }
        ]
    })["sections"][0]["items"][0]

    document["sections"][0]["items"].append(
        new_item
    )

    assert find_item(document, "late_item") is new_item
    assert get_value(document, "late_item") == 5
