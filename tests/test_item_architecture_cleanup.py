# -*- coding: utf-8 -*-

import os

import pytest

from script_toolbox.constants import CONFIG_VERSION
from script_toolbox.core.editor_document import EditorDocumentController
from script_toolbox.core.values import find_item
from script_toolbox.core.values import normalize_value
from script_toolbox.model import DocumentIndex
from script_toolbox.model import ITEM_TYPES
from script_toolbox.model import ItemTypeDefinition
from script_toolbox.model import ItemTypeRegistry
from script_toolbox.model import create_item
from script_toolbox.model import walk_items
from script_toolbox.model.bindings import binding_events
from script_toolbox.model.bindings import make_binding
from script_toolbox.model.fields import ChoiceField
from script_toolbox.model.fields import IntField
from script_toolbox.model.items import normalize_numeric_value
from script_toolbox.model.items import safe_float
from script_toolbox.model.items import safe_int
from script_toolbox.model.layouts import is_container_kind
from script_toolbox.model.layouts import is_layout_kind


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


def _source(*parts):
    path = os.path.join(ROOT, *parts)
    with open(path, "r") as handle:
        return handle.read()


def _nested_document():
    return {
        "version": CONFIG_VERSION,
        "sections": [
            create_item(
                "folder",
                {
                    "id": "root",
                    "name": "root",
                    "items": [
                        {
                            "kind": "column",
                            "id": "column_a",
                            "name": "column_a",
                            "items": [
                                {
                                    "kind": "button",
                                    "id": "button_a",
                                    "name": "button_a",
                                },
                                {
                                    "kind": "row",
                                    "id": "row_a",
                                    "name": "row_a",
                                    "items": [
                                        {
                                            "kind": "column",
                                            "id": "column_b",
                                            "name": "column_b",
                                            "items": [
                                                {
                                                    "kind": "button",
                                                    "id": "button_b",
                                                    "name": "button_b",
                                                    "bindings": [
                                                        make_binding(
                                                            "click",
                                                            script=(
                                                                "toolbox.find_item('button_a')"
                                                            ),
                                                            binding_id="link"
                                                        )
                                                    ],
                                                },
                                            ],
                                        },
                                    ],
                                },
                            ],
                        },
                        {
                            "kind": "button",
                            "id": "external",
                            "name": "external",
                            "bindings": [
                                make_binding(
                                    "click",
                                    script="toolbox.find_item('button_a')",
                                    binding_id="external_link"
                                )
                            ],
                        },
                    ],
                }
            )
        ],
    }


def test_registry_is_authoritative_for_builtins_and_capabilities():
    assert CONFIG_VERSION == 21
    assert ITEM_TYPES.get("button").title == "Button"
    assert ITEM_TYPES.get("image").category == "Display"
    assert ITEM_TYPES.get("folder").has_capability("section")
    assert ITEM_TYPES.get("column").is_container is True
    assert ITEM_TYPES.get("column").is_layout is True
    assert ITEM_TYPES.get("row").layout_axis == "horizontal"
    assert ITEM_TYPES.get("column").layout_axis == "vertical"
    assert ITEM_TYPES.get("button").is_container is False
    assert is_container_kind("folder") is True
    assert is_container_kind("row") is True
    assert is_container_kind("column") is True
    assert is_container_kind("button") is False
    assert is_layout_kind("row") is True
    assert is_layout_kind("column") is True


def test_registry_rejects_duplicates_and_unknown_required_kind():
    registry = ItemTypeRegistry()
    definition = ItemTypeDefinition("demo", "Demo")
    registry.register(definition)

    with pytest.raises(ValueError):
        registry.register(definition)
    assert registry.get("missing") is None
    with pytest.raises(ValueError):
        registry.get("missing", required=True)


def test_field_schema_defaults_clamps_choices_and_custom_normalizer():
    def normalize(props, raw):
        if props["low"] > props["high"]:
            props["low"], props["high"] = props["high"], props["low"]
        return props

    definition = ItemTypeDefinition(
        "demo",
        "Demo",
        fields={
            "low": IntField(default=0, minimum=-10, maximum=10),
            "high": IntField(default=5, minimum=-10, maximum=10),
            "mode": ChoiceField(("a", "b"), default="a"),
        },
        normalize_props=normalize,
    )
    props = definition.normalize_props({
        "low": 99,
        "high": -99,
        "mode": "invalid",
    })
    assert props == {"low": -10, "high": 10, "mode": "a"}


def test_universal_item_envelope_keeps_type_data_out_of_root():
    integer = create_item(
        "integer",
        {
            "id": "number",
            "name": "number",
            "ui": {"label": "Count"},
            "props": {
                "size": 3,
                "min": -10,
                "max": 10,
                "value": [99, "bad", -99],
            },
        }
    )

    assert set(integer.keys()) == set((
        "kind", "id", "name", "ui", "props", "bindings"
    ))
    assert integer["ui"]["label"] == "Count"
    assert integer["props"]["value"] == [10, 0, -10]
    assert "value" not in integer
    assert "min" not in integer

    row = create_item("row", {"items": [{"kind": "button"}]})
    assert "items" in row
    assert "items" not in create_item("button", {})


def test_walk_and_document_index_cover_nested_row_column_combinations():
    document = _nested_document()
    ids = [
        item["id"]
        for item in walk_items(document, include_folders=True)
    ]

    assert ids == [
        "root",
        "column_a",
        "button_a",
        "row_a",
        "column_b",
        "button_b",
        "external",
    ]

    index = DocumentIndex(document)
    assert index.find("column_b")["id"] == "column_b"
    assert index.find("button_b")["id"] == "button_b"


def test_base_editor_controller_handles_universal_container_topology_and_links():
    controller = EditorDocumentController(_nested_document())

    assert controller.find_by_id("button_b")["kind"] == "button"
    topology = controller.capture_topology()
    assert topology["children"]["root"] == ["column_a", "external"]
    assert topology["children"]["column_a"] == ["button_a", "row_a"]
    assert topology["children"]["row_a"] == ["column_b"]
    assert topology["children"]["column_b"] == ["button_b"]

    clone = controller.clone_subtree(
        controller.find_by_id("column_a")
    )
    cloned_a = clone["items"][0]
    cloned_b = clone["items"][1]["items"][0]["items"][0]
    clone_script = cloned_b["bindings"][0]["script"]

    assert cloned_a["id"] != "button_a"
    assert cloned_a["name"] != "button_a"
    assert cloned_a["id"] in clone_script
    assert "'button_a'" not in clone_script


def test_numeric_schema_and_store_normalization_share_contract():
    assert normalize_numeric_value(
        [99, "bad", -99],
        3,
        -10,
        10,
        safe_int,
        2
    ) == [10, 2, -10]

    integer = create_item(
        "integer",
        {
            "props": {
                "size": 3,
                "min": -10,
                "max": 10,
                "value": [99, "bad", -99],
            },
        }
    )
    assert integer["props"]["value"] == [10, 0, -10]
    assert normalize_value(integer, [8, "bad", -50]) == [8, 0, -10]

    scalar = create_item(
        "float",
        {
            "props": {
                "size": 1,
                "min": -1.0,
                "max": 1.0,
                "value": 9.0,
            },
        }
    )
    assert scalar["props"]["value"] == 1.0
    assert normalize_numeric_value(
        0.5,
        1,
        -1.0,
        1.0,
        safe_float,
        0.0
    ) == 0.5


def test_events_and_image_proof_are_registry_driven():
    image = create_item(
        "image",
        {
            "name": "reference_front",
            "props": {
                "source": "D:/refs/front.png",
                "fit": "cover",
                "width": 300,
                "height": 200,
            },
        }
    )
    assert image["props"]["fit"] == "cover"
    assert image["props"]["width"] == 300
    assert binding_events("image") == ("click", "double_click")
    assert ITEM_TYPES.get("image").fields["source"] is not None


def test_label_is_presentation_only_not_lookup_identity():
    item = create_item(
        "string",
        {
            "id": "item-id",
            "name": "symbolic_name",
            "ui": {"label": "Visible Label"},
            "props": {"value": "ok"},
        }
    )
    document = {
        "version": CONFIG_VERSION,
        "sections": [
            create_item("folder", {"items": [item]})
        ],
    }

    assert find_item(document, "item-id") is not None
    assert find_item(document, "symbolic_name") is not None
    assert find_item(document, "Visible Label") is None


def test_architecture_has_no_central_kind_extension_tables_or_flat_shims():
    items_source = _source(
        "scripts", "script_toolbox", "model", "items.py"
    )
    bindings_source = _source(
        "scripts", "script_toolbox", "model", "bindings.py"
    )
    layouts_source = _source(
        "scripts", "script_toolbox", "model", "layouts.py"
    )
    renderers_source = _source(
        "scripts", "script_toolbox", "ui", "runtime_renderers.py"
    )
    runtime_registry_source = _source(
        "scripts", "script_toolbox", "core", "runtime_registry.py"
    )
    property_registry_source = _source(
        "scripts", "script_toolbox", "ui", "properties", "registry.py"
    )
    palette_source = _source(
        "scripts", "script_toolbox", "ui", "item_palette.py"
    )
    editor_source = _source(
        "scripts", "script_toolbox", "ui", "interface_editor.py"
    )
    editor_layout_source = _source(
        "scripts", "script_toolbox", "ui", "layout_editor_adapter.py"
    )

    assert "_FACTORIES" not in items_source
    assert "EVENT_CAPABILITIES" not in bindings_source
    assert "STATE_TOGGLE_KINDS" not in bindings_source
    assert "CONTAINER_KINDS" not in layouts_source
    assert "LAYOUT_KINDS" not in layouts_source
    assert "entries = (" not in renderers_source
    assert "PROPERTY_EDITORS" not in property_registry_source
    assert "ITEM_KINDS" not in items_source
    assert "ITEM_TYPES.creatable()" in palette_source

    assert "ItemDataView" not in runtime_registry_source
    assert "item_view" not in runtime_registry_source
    assert "PALETTE_GROUPS" not in editor_source
    assert 'data["label"]' not in editor_source
    assert 'data["label"]' not in editor_layout_source
    assert 'kind == "folder"' not in editor_source
    assert 'kind == "row"' not in editor_source
    assert 'kind == "column"' not in editor_source
    assert 'kind == "folder"' not in editor_layout_source
    assert 'kind == "row"' not in editor_layout_source
    assert 'kind == "column"' not in editor_layout_source


def test_flat_item_compatibility_modules_are_removed():
    assert not os.path.exists(os.path.join(
        ROOT, "scripts", "script_toolbox", "model", "item_view.py"
    ))
    assert not os.path.exists(os.path.join(
        ROOT, "scripts", "script_toolbox", "ui", "item_runtime_adapter.py"
    ))


def test_old_text_item_factory_module_is_removed():
    assert not os.path.exists(os.path.join(
        ROOT, "scripts", "script_toolbox", "model", "text_item.py"
    ))
