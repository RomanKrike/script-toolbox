# -*- coding: utf-8 -*-

import script_toolbox.core.presets as presets_module
from script_toolbox.constants import CONFIG_VERSION
from script_toolbox.core.editor_document import EditorDocumentController
from script_toolbox.core.presets import build_preset_root
from script_toolbox.core.presets import get_preset
from script_toolbox.core.presets import iter_presets
from script_toolbox.model import walk_items


_VALID_DCCS = (
    "all",
    "maya",
    "houdini",
    "nuke",
    "blender",
)


def _items(root):
    document = {
        "version": CONFIG_VERSION,
        "sections": [root],
    }
    return list(
        walk_items(
            document,
            include_folders=True
        )
    )


def _by_name(root):
    return dict(
        (item["name"], item)
        for item in _items(root)
    )


def _registry_preset(preset_id, dcc, category="TEST"):
    return {
        "id": preset_id,
        "dcc": dcc,
        "category": category,
        "label": preset_id,
        "description": "Test preset {0}".format(preset_id),
        "root": {
            "kind": "folder",
            "id": "root_{0}".format(preset_id),
            "name": "root_{0}".format(preset_id),
            "label": preset_id,
            "items": [],
        },
    }


def _preset_ids(presets):
    return [
        preset["id"]
        for preset in presets
    ]


def test_builtin_presets_have_normalized_dcc_metadata():
    presets = iter_presets()

    assert presets
    for preset in presets:
        assert "dcc" in preset
        assert preset["dcc"] in _VALID_DCCS
        assert preset["dcc"] == preset["dcc"].lower()


def test_builtin_selection_set_is_a_normalized_self_contained_subtree():
    preset = get_preset("selection_set")
    root = build_preset_root("selection_set")

    assert preset["dcc"] == "all"
    assert preset["category"] == "SELECTION"
    assert root["kind"] == "folder"
    assert root["name"] == "selection_set"

    items = _by_name(root)
    assert items["selection_set_objects"]["kind"] == "field"
    assert items["selection_set_actions"]["kind"] == "row"

    add_script = items[
        "selection_set_add"
    ]["bindings"][0]["script"]
    assert "host.current_selection(long_names=True)" in add_script
    assert (
        'toolbox.add_to_field("selection_set_objects", '
        in add_script
    )


def test_iter_presets_preserves_unfiltered_contract_and_filters_by_dcc(
    monkeypatch
):
    registry = (
        _registry_preset("universal", "all", "COMMON"),
        _registry_preset("maya_only", "maya", "SELECTION"),
        _registry_preset("houdini_only", "houdini", "CACHE"),
    )
    monkeypatch.setattr(
        presets_module,
        "_BUILTIN_PRESETS",
        registry
    )

    assert _preset_ids(iter_presets()) == [
        "universal",
        "maya_only",
        "houdini_only",
    ]
    assert _preset_ids(iter_presets("maya")) == [
        "universal",
        "maya_only",
    ]
    assert _preset_ids(iter_presets("MAYA")) == [
        "universal",
        "maya_only",
    ]
    assert _preset_ids(iter_presets("houdini")) == [
        "universal",
        "houdini_only",
    ]


def test_unknown_host_receives_only_universal_presets(monkeypatch):
    registry = (
        _registry_preset("universal", "all"),
        _registry_preset("maya_only", "maya"),
        _registry_preset("houdini_only", "houdini"),
    )
    monkeypatch.setattr(
        presets_module,
        "_BUILTIN_PRESETS",
        registry
    )

    assert _preset_ids(iter_presets("standalone")) == [
        "universal",
    ]
    assert _preset_ids(iter_presets("unknown-host")) == [
        "universal",
    ]


def test_repeated_preset_clone_remaps_internal_script_links():
    source = build_preset_root("selection_set")

    empty_controller = EditorDocumentController({
        "version": CONFIG_VERSION,
        "sections": [],
    })
    first = empty_controller.clone_subtree(
        source
    )

    controller = EditorDocumentController({
        "version": CONFIG_VERSION,
        "sections": [first],
    })
    second = controller.clone_subtree(
        build_preset_root("selection_set")
    )

    first_items = _by_name(first)
    second_items = _by_name(second)

    assert "selection_set_objects" in first_items
    assert "selection_set_objects_2" in second_items

    first_ids = set(
        item["id"]
        for item in _items(first)
    )
    second_ids = set(
        item["id"]
        for item in _items(second)
    )
    assert not first_ids.intersection(second_ids)

    for button_name in (
        "selection_set_add_2",
        "selection_set_remove_2",
        "selection_set_select_2",
        "selection_set_clear_2",
    ):
        script = second_items[
            button_name
        ]["bindings"][0]["script"]
        assert '"selection_set_objects_2"' in script
        assert '"selection_set_objects"' not in script


def test_preset_registry_returns_defensive_copies():
    presets = iter_presets()
    presets[0]["label"] = "Changed"

    assert get_preset("selection_set")["label"] == "Selection Set"
    assert build_preset_root("missing") is None
