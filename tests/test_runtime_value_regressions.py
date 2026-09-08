# -*- coding: utf-8 -*-

from copy import deepcopy
from pathlib import Path

from script_toolbox.core.config import load_config
from script_toolbox.core.values import find_item
from script_toolbox.core.values import get_value
from script_toolbox.core.values import store_value
from script_toolbox.model import walk_items


FIXTURE = (
    Path(__file__).resolve().parent /
    "fixtures" /
    "golden_v16_full.json"
)


def _document():
    return load_config(
        path=str(FIXTURE)
    )


def _structure_snapshot(document):
    return [
        (
            item["id"],
            item["name"],
            item["kind"],
        )
        for item in walk_items(
            document,
            include_folders=True
        )
    ]


def test_runtime_lookup_by_id_name_and_label_targets_same_item():
    document = _document()

    by_id = find_item(document, "integer_samples")
    by_name = find_item(document, "samples")
    by_label = find_item(document, "Samples")

    assert by_id is by_name
    assert by_name is by_label


def test_runtime_get_value_returns_copy_for_mutable_values():
    document = _document()

    values = get_value(document, "nodes")
    values.append("pCone1")

    assert get_value(document, "nodes") == [
        "pCube1",
        "pSphere1",
    ]


def test_runtime_value_normalization_matches_current_contract():
    document = _document()

    store_value(document, "samples", 999)
    store_value(document, "exposure", -999)
    store_value(document, "quality", "Unknown")
    store_value(document, "tint", [-1, 0.25, 2])
    store_value(document, "nodes", ("a", 2, "c"))

    assert get_value(document, "samples") == 64
    assert get_value(document, "exposure") == -10.0
    assert get_value(document, "quality") == "Draft"
    assert get_value(document, "tint") == [0.0, 0.25, 1.0]
    assert get_value(document, "nodes") == ["a", "2", "c"]


def test_runtime_value_edits_do_not_change_document_structure():
    document = _document()
    before = _structure_snapshot(document)

    for value in range(-25, 100):
        store_value(document, "samples", value)

    store_value(document, "asset_name", "Hydra")
    store_value(document, "enabled", False)
    store_value(document, "quality", "Final")

    after = _structure_snapshot(document)

    assert after == before
    assert get_value(document, "samples") == 64
    assert get_value(document, "asset_name") == "Hydra"
    assert get_value(document, "enabled") is False
    assert get_value(document, "quality") == "Final"


def test_runtime_unknown_or_non_value_items_are_noops():
    document = _document()
    before = deepcopy(document)

    assert store_value(document, "missing_item", 10) is None
    assert store_value(document, "render_state", True) is None
    assert get_value(document, "render_state", "fallback") == "fallback"

    assert document == before
