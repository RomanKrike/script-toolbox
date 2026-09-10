# -*- coding: utf-8 -*-

import json
from pathlib import Path

import pytest

from script_toolbox.constants import CONFIG_VERSION
from script_toolbox.core.config import load_config
from script_toolbox.core.config import save_config
from script_toolbox.core.migrations import UnsupportedConfigVersionError
from script_toolbox.core.values import find_item
from script_toolbox.model import walk_items


FIXTURES = Path(__file__).resolve().parent / "fixtures"


def fixture_path(name):
    return FIXTURES / name


def test_current_golden_config_round_trip_is_idempotent(tmp_path):
    document = load_config(
        path=str(fixture_path("golden_v20_current.json"))
    )
    output = tmp_path / "round_trip.json"

    save_config(document, path=str(output))
    reloaded = load_config(path=str(output))

    assert reloaded == document
    assert reloaded["version"] == CONFIG_VERSION

    with output.open("r", encoding="utf-8") as handle:
        serialized = json.load(handle)

    assert serialized == document


def test_current_golden_config_preserves_native_kinds_and_nested_order():
    document = load_config(
        path=str(fixture_path("golden_v20_current.json"))
    )

    snapshot = [
        (item["name"], item["kind"])
        for item in walk_items(document)
    ]

    assert snapshot == [
        ("asset_name", "string"),
        ("samples", "integer"),
        ("status_icon", "icon"),
        ("render_state", "toggle_button"),
        ("actions", "row"),
        ("run_render", "button"),
        ("values", "column"),
        ("selection", "field"),
    ]

    assert find_item(document, "status_icon")["content_alignment"] == "center"
    assert find_item(document, "render_state")["kind"] == "toggle_button"


def test_current_golden_config_has_unique_stable_ids():
    document = load_config(
        path=str(fixture_path("golden_v20_current.json"))
    )
    ids = [
        item["id"]
        for item in walk_items(
            document,
            include_folders=True
        )
    ]

    assert len(ids) == len(set(ids))
    assert ids[0] == "folder_main"
    assert "toggle_render" in ids
    assert "column_values" in ids


def test_old_schema_is_rejected_instead_of_migrated(tmp_path):
    path = tmp_path / "old.json"
    path.write_text(
        json.dumps({
            "version": CONFIG_VERSION - 1,
            "sections": [],
        }),
        encoding="utf-8"
    )

    with pytest.raises(UnsupportedConfigVersionError):
        load_config(path=str(path))
