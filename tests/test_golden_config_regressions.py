# -*- coding: utf-8 -*-

import json
from pathlib import Path

from script_toolbox.constants import CONFIG_VERSION
from script_toolbox.core.config import load_config
from script_toolbox.core.config import save_config
from script_toolbox.core.values import find_item
from script_toolbox.model import walk_items


FIXTURES = Path(__file__).resolve().parent / "fixtures"


def fixture_path(name):
    return FIXTURES / name


def test_full_v16_golden_config_round_trip_is_idempotent(tmp_path):
    document = load_config(
        path=str(fixture_path("golden_v16_full.json"))
    )
    output = tmp_path / "round_trip.json"

    save_config(
        document,
        path=str(output)
    )

    reloaded = load_config(
        path=str(output)
    )

    assert reloaded == document

    with output.open("r", encoding="utf-8") as handle:
        serialized = json.load(handle)

    assert serialized == document


def test_full_v16_golden_config_preserves_kind_and_traversal_order():
    document = load_config(
        path=str(fixture_path("golden_v16_full.json"))
    )

    snapshot = [
        (item["name"], item["kind"])
        for item in walk_items(document)
    ]

    assert snapshot == [
        ("header", "label"),
        ("asset_name", "string"),
        ("samples", "integer"),
        ("exposure", "float"),
        ("enabled", "checkbox"),
        ("quality", "menu"),
        ("tint", "color"),
        ("nodes", "field"),
        ("render_state", "button"),
        ("actions", "row"),
        ("run_render", "button"),
        ("frames", "integer"),
        ("selection", "field"),
        ("advanced_separator", "separator"),
        ("cleanup", "button"),
    ]


def test_full_v16_golden_config_keeps_all_ids_unique_and_stable():
    document = load_config(
        path=str(fixture_path("golden_v16_full.json"))
    )
    ids = [
        item["id"]
        for item in walk_items(
            document,
            include_folders=True
        )
    ]

    assert len(ids) == 18
    assert len(set(ids)) == len(ids)
    assert ids[0] == "folder_main"
    assert ids[-1] == "button_cleanup"
    assert "folder_advanced" in ids
    assert "folder_secondary" in ids


def test_legacy_v15_golden_config_migrates_and_normalizes_payload():
    document = load_config(
        path=str(fixture_path("golden_v15_legacy.json"))
    )

    assert document["version"] == CONFIG_VERSION
    assert document["sections"][0]["name"] == "legacy_tools"

    toggle = find_item(document, "legacy_enabled")
    assert toggle["kind"] == "checkbox"
    assert toggle["label_position"] == "left"
    assert toggle["value"] is True

    menu = find_item(document, "legacy_quality")
    assert menu["items"] == ["Low", "Medium", "High"]
    assert menu["value"] == "Low"

    integer = find_item(document, "legacy_samples")
    assert integer["min"] == 1
    assert integer["max"] == 8
    assert integer["step"] == 1
    assert integer["value"] == 8

    button = find_item(document, "legacy_action")
    assert button["click_script"] == "print('legacy payload')"
    assert button["shift_script"] == "print('legacy alternate')"


def test_legacy_migration_becomes_stable_current_schema(tmp_path):
    migrated = load_config(
        path=str(fixture_path("golden_v15_legacy.json"))
    )
    output = tmp_path / "migrated.json"

    save_config(
        migrated,
        path=str(output)
    )

    reloaded = load_config(
        path=str(output)
    )

    assert reloaded == migrated
    assert reloaded["version"] == CONFIG_VERSION
