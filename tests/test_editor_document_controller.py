# -*- coding: utf-8 -*-

import copy
import json
import os

from script_toolbox.core.editor_document import EditorDocumentController
from script_toolbox.model import walk_items


FIXTURES = os.path.join(
    os.path.dirname(__file__),
    "fixtures"
)


def _golden_document():
    path = os.path.join(
        FIXTURES,
        "golden_v16_full.json"
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


def test_controller_owns_defensive_copy_and_indexes_nested_items():
    source = _golden_document()
    controller = EditorDocumentController(source)

    source["sections"][0]["label"] = "Changed outside"

    assert controller.document["sections"][0]["label"] != "Changed outside"
    assert controller.find_by_id("int_samples")["name"] == "samples"
    assert controller.find_by_id("field_selection")["kind"] == "field"


def test_snapshot_is_independent_from_staged_document():
    controller = EditorDocumentController(
        _golden_document()
    )

    snapshot = controller.snapshot()
    snapshot["sections"][0]["label"] = "Snapshot only"

    assert controller.document["sections"][0]["label"] != "Snapshot only"


def test_adopt_preserves_item_identity_for_qt_tree_sync():
    controller = EditorDocumentController(
        _golden_document()
    )
    item = controller.find_by_id("int_samples")

    adopted = {
        "version": controller.document["version"],
        "sections": controller.document["sections"],
    }
    controller.adopt(adopted)

    assert controller.find_by_id("int_samples") is item
    assert controller.document is adopted


def test_replace_rebuilds_index_and_drops_old_ids():
    controller = EditorDocumentController(
        _golden_document()
    )
    replacement = copy.deepcopy(
        controller.document
    )
    replacement["sections"][0]["items"] = []

    controller.replace(replacement)

    assert controller.find_by_id("int_samples") is None
    assert controller.find_by_id(
        replacement["sections"][0]["id"]
    ) is not None


def test_unique_name_matches_legacy_suffix_and_sanitization_contract():
    controller = EditorDocumentController(
        _golden_document()
    )
    used = set(["render_tools", "render_tools_2"])

    assert controller.unique_name(
        "Render Tools!",
        used
    ) == "Render_Tools"
    assert controller.unique_name(
        "render_tools",
        used
    ) == "render_tools_3"


def test_clone_subtree_allocates_fresh_ids_and_unique_names_recursively():
    controller = EditorDocumentController(
        _golden_document()
    )
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


def test_cache_subtree_supports_detached_items_before_tree_sync():
    controller = EditorDocumentController(
        _golden_document()
    )
    detached = controller.clone_subtree(
        controller.document["sections"][0]
    )

    assert controller.find_by_id(detached["id"]) is None

    controller.cache_subtree(detached)

    assert controller.find_by_id(detached["id"]) is detached
    first_child = detached["items"][0]
    assert controller.find_by_id(first_child["id"]) is first_child


def test_duplicate_name_reports_first_duplicate_in_document_traversal():
    document = _golden_document()
    controller = EditorDocumentController(document)
    items = _all_items(controller.document)

    items[1]["name"] = items[0]["name"]

    assert controller.duplicate_name() == items[0]["name"]
