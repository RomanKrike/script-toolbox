# -*- coding: utf-8 -*-

import os

from script_toolbox.constants import CONFIG_VERSION
from script_toolbox.core.editor_document import EditorDocumentController
from script_toolbox.core.values import find_item
from script_toolbox.core.values import normalize_value
from script_toolbox.model import DocumentIndex
from script_toolbox.model import create_item
from script_toolbox.model import walk_items
from script_toolbox.model.bindings import make_binding
from script_toolbox.model.items import get_item_factory
from script_toolbox.model.items import normalize_numeric_value
from script_toolbox.model.items import safe_float
from script_toolbox.model.items import safe_int
from script_toolbox.model.layouts import is_container_kind


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


def test_container_contract_and_factories_are_model_owned():
    assert is_container_kind("folder") is True
    assert is_container_kind("row") is True
    assert is_container_kind("column") is True
    assert is_container_kind("button") is False
    assert get_item_factory("column") is not None
    assert get_item_factory("toggle_button") is not None
    assert get_item_factory("toggle_icon") is not None
    assert create_item("column", {})["kind"] == "column"


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


def test_base_editor_controller_handles_column_cache_topology_and_clone_links():
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

    external_script = controller.find_by_id(
        "external"
    )["bindings"][0]["script"]
    assert external_script == "toolbox.find_item('button_a')"

    controller.cache_subtree(clone)
    assert controller.find_by_id(cloned_b["id"]) is cloned_b


def test_base_editor_controller_renames_references_inside_columns():
    controller = EditorDocumentController(_nested_document())
    target = controller.find_by_id("button_a")
    target["name"] = "button_renamed"

    changed = controller.rename_item_references(
        "button_a",
        "button_a",
        "button_renamed"
    )

    assert "button_b" in changed
    assert "external" in changed
    assert "button_renamed" in controller.find_by_id(
        "button_b"
    )["bindings"][0]["script"]


def test_numeric_factory_and_store_normalization_share_contract():
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
            "size": 3,
            "min": -10,
            "max": 10,
            "value": [99, "bad", -99],
        }
    )
    assert integer["value"] == [10, 0, -10]
    assert normalize_value(integer, [8, "bad", -50]) == [8, 0, -10]

    scalar = create_item(
        "float",
        {
            "size": 1,
            "min": -1.0,
            "max": 1.0,
            "value": 9.0,
        }
    )
    assert scalar["value"] == 1.0
    assert normalize_numeric_value(
        0.5,
        1,
        -1.0,
        1.0,
        safe_float,
        0.0
    ) == 0.5


def test_icon_alignment_uses_only_canonical_key():
    old_key = create_item(
        "icon",
        {"alignment": "right"}
    )
    current = create_item(
        "icon",
        {"content_alignment": "center"}
    )

    assert old_key["content_alignment"] == "left"
    assert "alignment" not in old_key
    assert current["content_alignment"] == "center"


def test_label_is_presentation_only_not_lookup_identity():
    item = create_item(
        "string",
        {
            "id": "item-id",
            "name": "symbolic_name",
            "label": "Visible Label",
            "value": "ok",
        }
    )
    document = {
        "version": CONFIG_VERSION,
        "sections": [
            create_item(
                "folder",
                {"items": [item]}
            )
        ],
    }

    assert find_item(document, "item-id") is not None
    assert find_item(document, "symbolic_name") is not None
    assert find_item(document, "Visible Label") is None


def test_architecture_has_no_legacy_runtime_or_model_paths():
    layouts_source = _source(
        "scripts", "script_toolbox", "model", "layouts.py"
    )
    items_source = _source(
        "scripts", "script_toolbox", "model", "items.py"
    )
    bindings_source = _source(
        "scripts", "script_toolbox", "model", "bindings.py"
    )
    runtime_source = _source(
        "scripts", "script_toolbox", "ui", "runtime.py"
    )
    renderers_source = _source(
        "scripts", "script_toolbox", "ui", "runtime_renderers.py"
    )
    references_source = _source(
        "scripts", "script_toolbox", "core", "references.py"
    )
    controller_source = _source(
        "scripts", "script_toolbox", "core", "editor_document.py"
    )

    assert "items_module.walk_items =" not in layouts_source
    assert "items_module.create_item =" not in layouts_source
    assert "._FACTORIES[" not in layouts_source
    assert "LEGACY_CALLBACK_EVENT_MAP" not in bindings_source
    assert "click_script" not in bindings_source
    assert "shift_script" not in bindings_source
    assert "on_change_script" not in bindings_source
    assert '"toggle":' not in items_source
    assert '"section":' not in items_source
    assert 'data.get("folders")' not in items_source
    assert "RuntimeSection" not in runtime_source
    assert "_LEGACY_BUILD" not in renderers_source
    assert "install_runtime_renderer_registry" not in renderers_source
    assert '("folder", "row")' not in references_source
    assert '("folder", "row")' not in controller_source
    assert "is_container_kind" in references_source
    assert "is_container_kind" in controller_source

    assert not os.path.exists(os.path.join(
        ROOT, "scripts", "script_toolbox", "model", "callbacks.py"
    ))
    assert not os.path.exists(os.path.join(
        ROOT, "scripts", "script_toolbox", "model", "toggle_button.py"
    ))
    assert not os.path.exists(os.path.join(
        ROOT, "scripts", "script_toolbox", "model", "toggle_icon.py"
    ))
    assert not os.path.exists(os.path.join(
        ROOT, "scripts", "script_toolbox", "core", "layout_document.py"
    ))
