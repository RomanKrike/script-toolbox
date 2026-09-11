# -*- coding: utf-8 -*-

from script_toolbox.constants import CONFIG_VERSION
from script_toolbox.core.editor_document import EditorDocumentController
from script_toolbox.core.presets import build_preset_root
from script_toolbox.core.presets import get_preset
from script_toolbox.core.presets import iter_presets
from script_toolbox.model import walk_items


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


def test_builtin_selection_set_is_a_normalized_self_contained_subtree():
    preset = get_preset("selection_set")
    root = build_preset_root("selection_set")

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
