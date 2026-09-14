# -*- coding: utf-8 -*-

import json

import pytest

from script_toolbox.constants import CONFIG_VERSION
from script_toolbox.core.config import ConfigRecoveryRequired
from script_toolbox.core.config import load_config
from script_toolbox.core.values import get_value
from script_toolbox.core.values import store_value
from script_toolbox.model import ItemValidationError
from script_toolbox.model import create_item
from script_toolbox.model import normalize_document
from script_toolbox.model import normalize_item_props


def _image_data(width="64"):
    return {
        "kind": "image",
        "id": "image_preview",
        "name": "preview",
        "ui": {},
        "props": {
            "source": "preview.png",
            "fit": "contain",
            "width": width,
            "height": "48",
        },
        "bindings": [],
    }


def test_create_item_coerces_supported_values_and_rejects_corruption():
    image = create_item("image", _image_data(width="64"))
    assert image["props"]["width"] == 64
    assert image["props"]["height"] == 48

    bad = _image_data(width="abc")
    with pytest.raises(ItemValidationError) as caught:
        create_item("image", bad)

    error = caught.value
    assert error.kind == "image"
    assert error.field == "width"
    assert error.value == "abc"
    assert error.item_id == "image_preview"
    assert error.item_name == "preview"


def test_normalize_item_props_is_the_single_editor_style_canonicalizer():
    item = create_item("image", _image_data(width=64))
    item["props"]["width"] = "128"
    item["props"]["fit"] = "COVER"

    normalized = normalize_item_props(item)

    assert normalized is item["props"]
    assert item["props"]["width"] == 128
    assert item["props"]["fit"] == "cover"

    item["props"]["width"] = "broken"
    with pytest.raises(ItemValidationError):
        normalize_item_props(item)


def test_normalize_document_rejects_malformed_current_schema_item():
    document = {
        "version": CONFIG_VERSION,
        "sections": [
            create_item(
                "folder",
                {
                    "id": "section",
                    "name": "section",
                    "items": [_image_data(width=64)],
                },
            )
        ],
    }
    document["sections"][0]["items"][0]["props"]["width"] = "broken"

    with pytest.raises(ItemValidationError) as caught:
        normalize_document(document)

    assert caught.value.kind == "image"
    assert caught.value.field == "width"


def test_config_load_rejects_malformed_current_schema_without_silent_default(
    tmp_path
):
    section = create_item(
        "folder",
        {
            "id": "section",
            "name": "section",
            "items": [_image_data(width=64)],
        },
    )
    section["items"][0]["props"]["width"] = "broken"
    path = tmp_path / "invalid_current.json"
    path.write_text(
        json.dumps({
            "version": CONFIG_VERSION,
            "sections": [section],
        }),
        encoding="utf-8"
    )

    with pytest.raises(ConfigRecoveryRequired) as caught:
        load_config(path=str(path))

    assert "image" in caught.value.cause
    assert "width" in caught.value.cause
    assert "broken" in caught.value.cause


def test_runtime_value_write_uses_same_schema_and_is_transactional_on_error():
    checkbox = create_item(
        "checkbox",
        {
            "id": "enabled-id",
            "name": "enabled",
            "props": {"value": False},
        },
    )
    document = {
        "version": CONFIG_VERSION,
        "sections": [
            create_item(
                "folder",
                {
                    "id": "section",
                    "name": "section",
                    "items": [checkbox],
                },
            )
        ],
    }

    store_value(document, "enabled", "false")
    assert get_value(document, "enabled") is False
    store_value(document, "enabled", "yes")
    assert get_value(document, "enabled") is True

    with pytest.raises(ItemValidationError):
        store_value(document, "enabled", "not-a-bool")
    assert get_value(document, "enabled") is True


def test_unknown_persisted_kind_remains_invalid_without_placeholder_layer():
    document = {
        "version": CONFIG_VERSION,
        "sections": [
            {
                "kind": "future_plugin_type",
                "id": "future",
                "name": "future",
                "ui": {},
                "props": {},
                "bindings": [],
                "items": [],
            },
        ],
    }

    with pytest.raises(ItemValidationError) as caught:
        normalize_document(document)
    assert caught.value.kind == "future_plugin_type"
