# -*- coding: utf-8 -*-

import copy
import json
import os

from script_toolbox.constants import CONFIG_VERSION
from script_toolbox.core.editor_document import EditorDocumentController
from script_toolbox.model import walk_items
from script_toolbox.model.bindings import make_binding


FIXTURES = os.path.join(
    os.path.dirname(__file__),
    "fixtures"
)


def _current_document():
    path = os.path.join(
        FIXTURES,
        "current_v20_full.json"
    )
    with open(path, "r") as handle:
        return json.load(handle)


def _all_items(document):
    return list(
        walk_items(
            document,
            include_folders=True
        )
    )


def _linked_document():
    return {
        "version": CONFIG_VERSION,
        "sections": [
            {
                "kind": "folder",
                "id": "folder_group",
                "name": "group",
                "label": "Group",
                "items": [
                    {
                        "kind": "string",
                        "id": "field_internal_id",
                        "name": "internal_value",
                        "label": "Internal",
                        "value": "inside",
                    },
                    {
                        "kind": "button",
                        "id": "button_internal_id",
                        "name": "run_internal",
                        "label": "Run",
                        "bindings": [
                            make_binding(
                                "click",
                                script="\n".join([
                                    "a = toolbox.get_value('internal_value')",
                                    "b = toolbox.get_value('field_internal_id')",
                                    "c = toolbox.get_value('external_value')",
                                    "note = 'internal_value'",
                                ]),
                                binding_id="internal_click"
                            )
                        ],
                    },
                ],
            },
            {
                "kind": "folder",
                "id": "folder_external",
                "name": "external_group",
                "label": "External",
                "items": [
                    {
                        "kind": "string",
                        "id": "field_external_id",
                        "name": "external_value",
                        "label": "External",
                        "value": "outside",
                    },
                    {
                        "kind": "button",
                        "id": "button_external_id",
                        "name": "external_reader",
                        "label": "External Reader",
                        "bindings": [
                            make_binding(
                                "click",
                                script="toolbox.get_value('internal_value')",
                                binding_id="external_click"
                            )
                        ],
                    },
                ],
            },
        ],
    }


def test_controller_owns_defensive_copy_and_indexes_nested_items():
    source = _current_document()
    controller = EditorDocumentController(source)

    source["sections"][0]["label"] = "Changed outside"

    assert controller.document["sections"][0]["label"] != "Changed outside"
    assert controller.find_by_id("integer_samples")["name"] == "samples"
    assert controller.find_by_id("field_selection")["kind"] == "field"


def test_snapshot_is_independent_from_staged_document():
    controller = EditorDocumentController(_current_document())

    snapshot = controller.snapshot()
    snapshot["sections"][0]["label"] = "Snapshot only"

    assert controller.document["sections"][0]["label"] != "Snapshot only"


def test_adopt_preserves_item_identity_for_qt_tree_sync():
    controller = EditorDocumentController(_current_document())
    item = controller.find_by_id("integer_samples")

    adopted = {
        "version": controller.document["version"],
        "sections": controller.document["sections"],
    }
    controller.adopt(adopted)

    assert controller.find_by_id("integer_samples") is item
    assert controller.document is adopted


def test_replace_rebuilds_index_and_drops_old_ids():
    controller = EditorDocumentController(_current_document())
    replacement = copy.deepcopy(controller.document)
    replacement["sections"][0]["items"] = []

    controller.replace(replacement)

    assert controller.find_by_id("integer_samples") is None
    assert controller.find_by_id(replacement["sections"][0]["id"]) is not None


def test_unique_name_suffix_and_sanitization_contract():
    controller = EditorDocumentController(_current_document())
    used = set(["render_tools", "render_tools_2"])

    assert controller.unique_name("Render Tools!", used) == "Render_Tools"
    assert controller.unique_name("render_tools", used) == "render_tools_3"


def test_clone_subtree_allocates_fresh_ids_and_unique_names_recursively():
    controller = EditorDocumentController(_current_document())
    source = controller.document["sections"][0]
    clone = controller.clone_subtree(source)

    original_items = _all_items({
        "version": controller.document["version"],
        "sections": [source],
    })
    clone_items = _all_items({
        "version": controller.document["version"],
        "sections": [clone],
    })

    original_ids = set(item["id"] for item in original_items)
    clone_ids = [item["id"] for item in clone_items]
    original_names = set(item["name"] for item in _all_items(controller.document))
    clone_names = [item["name"] for item in clone_items]

    assert not original_ids.intersection(clone_ids)
    assert len(clone_ids) == len(set(clone_ids))
    assert len(clone_names) == len(set(clone_names))
    assert not original_names.intersection(clone_names)
    assert clone["label"] == source["label"]
    assert clone["kind"] == source["kind"]


def test_clone_subtree_remaps_internal_binding_links_only():
    controller = EditorDocumentController(_linked_document())
    source = controller.document["sections"][0]
    clone = controller.clone_subtree(source)

    cloned_field = clone["items"][0]
    cloned_button = clone["items"][1]
    script = cloned_button["bindings"][0]["script"]

    assert cloned_field["name"] == "internal_value_2"
    assert cloned_field["id"] != "field_internal_id"
    assert "toolbox.get_value('internal_value_2')" in script
    assert "toolbox.get_value('{0}')".format(cloned_field["id"]) in script
    assert "toolbox.get_value('external_value')" in script
    assert "note = 'internal_value'" in script


def test_rename_item_references_updates_managed_binding_calls():
    controller = EditorDocumentController(_linked_document())
    target = controller.find_by_id("field_internal_id")
    target["name"] = "renamed_value"

    changed_ids = controller.rename_item_references(
        "field_internal_id",
        "internal_value",
        "renamed_value"
    )

    internal_script = controller.find_by_id(
        "button_internal_id"
    )["bindings"][0]["script"]
    external_script = controller.find_by_id(
        "button_external_id"
    )["bindings"][0]["script"]

    assert changed_ids == set(["button_internal_id", "button_external_id"])
    assert "toolbox.get_value('renamed_value')" in internal_script
    assert "toolbox.get_value('renamed_value')" in external_script
    assert "note = 'internal_value'" in internal_script


def test_rename_item_references_rejects_unknown_stable_id():
    controller = EditorDocumentController(_linked_document())

    changed_ids = controller.rename_item_references(
        "missing_id",
        "internal_value",
        "renamed_value"
    )

    assert changed_ids == set()
    assert controller.find_by_id(
        "button_external_id"
    )["bindings"][0]["script"] == "toolbox.get_value('internal_value')"


def test_cache_subtree_supports_detached_items_before_tree_sync():
    controller = EditorDocumentController(_current_document())
    detached = controller.clone_subtree(
        controller.document["sections"][0]
    )

    assert controller.find_by_id(detached["id"]) is None

    controller.cache_subtree(detached)

    assert controller.find_by_id(detached["id"]) is detached
    first_child = detached["items"][0]
    assert controller.find_by_id(first_child["id"]) is first_child


def test_duplicate_name_reports_first_duplicate_in_document_traversal():
    document = _current_document()
    controller = EditorDocumentController(document)
    items = _all_items(controller.document)

    items[1]["name"] = items[0]["name"]

    assert controller.duplicate_name() == items[0]["name"]
