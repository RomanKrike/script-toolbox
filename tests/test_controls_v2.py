# -*- coding: utf-8 -*-

from script_toolbox.constants import CONFIG_VERSION
from script_toolbox.constants import ITEM_KINDS
from script_toolbox.core.references import rewrite_item_references
from script_toolbox.core.references import rewrite_subtree_references
from script_toolbox.core.values import store_value
from script_toolbox.model.bindings import binding_events
from script_toolbox.model.bindings import matching_bindings
from script_toolbox.model.items import create_item


def _document_with(item):
    return {
        "version": CONFIG_VERSION,
        "sections": [
            create_item(
                "folder",
                {
                    "id": "root",
                    "name": "root",
                    "items": [item],
                }
            )
        ],
    }


def test_controls_v2_schema_and_action_kinds_are_registered():
    assert CONFIG_VERSION == 20
    assert "icon" in ITEM_KINDS
    assert "toggle_button" in ITEM_KINDS
    assert "toggle_icon" in ITEM_KINDS
    assert "column" in ITEM_KINDS


def test_icon_model_preserves_current_alignment_and_binding():
    item = create_item(
        "icon",
        {
            "id": "icon_test",
            "name": "icon_test",
            "path": "$HOME/icon.png",
            "width": 32,
            "height": 40,
            "content_alignment": "center",
            "tooltip": "Open",
            "bindings": [
                {
                    "id": "open",
                    "event": "click",
                    "mouse_button": "left",
                    "modifiers": [],
                    "language": "python",
                    "script": "toolbox.get_value('target')",
                }
            ],
        }
    )

    assert item["kind"] == "icon"
    assert item["show_label"] is False
    assert item["path"] == "$HOME/icon.png"
    assert item["width"] == 32
    assert item["height"] == 40
    assert item["content_alignment"] == "center"
    assert "alignment" not in item
    assert item["tooltip"] == "Open"
    assert item["bindings"][0]["script"] == (
        "toolbox.get_value('target')"
    )


def test_button_icon_properties_and_icon_only_are_normalized():
    item = create_item(
        "button",
        {
            "icon_path": "icons/run.png",
            "icon_size": 28,
            "icon_only": True,
        }
    )

    assert item["icon_path"] == "icons/run.png"
    assert item["icon_size"] == 28
    assert item["icon_only"] is True
    assert len(item["bindings"]) == 1
    assert item["bindings"][0]["handler"] == "script"


def test_binding_events_are_kind_specific_and_layout_is_hidden():
    assert binding_events("integer") == (
        "value_changed",
        "editing_finished",
        "click",
        "double_click",
    )
    assert binding_events("field") == (
        "value_changed",
        "selection_changed",
        "click",
        "double_click",
    )
    assert binding_events("toggle_button") == (
        "click",
        "double_click",
    )
    assert binding_events("toggle_icon") == (
        "click",
        "double_click",
    )
    assert binding_events("folder") == ()
    assert binding_events(
        "folder",
        include_internal=True
    ) == (
        "opened",
        "closed",
    )
    assert binding_events("column") == ()
    assert binding_events("separator") == ()


def test_old_direct_script_field_is_not_converted_to_binding():
    item = create_item(
        "string",
        {
            "on_change_script": "result = value",
        }
    )

    assert item["bindings"] == []
    assert "on_change_script" not in item


def test_integer_vector_size_and_component_labels():
    item = create_item(
        "integer",
        {
            "size": 3,
            "value": [1, 2, 30],
            "min": 0,
            "max": 10,
            "component_labels": ["U", "V", "W"],
            "show_slider": True,
        }
    )

    assert item["size"] == 3
    assert item["value"] == [1, 2, 10]
    assert item["component_labels"] == ["U", "V", "W"]
    assert item["show_slider"] is True


def test_float_vector_defaults_missing_component_labels():
    item = create_item(
        "float",
        {
            "size": 4,
            "value": 1.5,
            "component_labels": ["R", "G"],
        }
    )

    assert item["size"] == 4
    assert item["value"] == [1.5, 1.5, 1.5, 1.5]
    assert item["component_labels"] == ["R", "G", "Z", "W"]


def test_scalar_numeric_contract_is_preserved_for_size_one():
    integer = create_item(
        "integer",
        {
            "size": 1,
            "value": [7, 8],
        }
    )
    floating = create_item(
        "float",
        {
            "size": 1,
            "value": 2.5,
        }
    )

    assert integer["value"] == 7
    assert floating["value"] == 2.5


def test_store_value_vector_clamps_each_component():
    item = create_item(
        "integer",
        {
            "id": "coords",
            "name": "coords",
            "size": 3,
            "min": 0,
            "max": 10,
            "value": [1, 2, 3],
        }
    )
    document = _document_with(item)

    stored = store_value(
        document,
        "coords",
        [-5, 5, 25]
    )

    assert stored["value"] == [0, 5, 10]


def test_binding_references_are_remapped_but_plain_strings_are_not():
    item = create_item(
        "string",
        {
            "id": "source",
            "name": "source",
            "bindings": [
                {
                    "id": "changed",
                    "event": "value_changed",
                    "language": "python",
                    "script": (
                        "value = toolbox.get_value('old_name')\n"
                        "note = 'old_name'\n"
                    ),
                }
            ],
        }
    )

    assert rewrite_item_references(
        item,
        {"old_name": "new_name"}
    ) is True

    source = item["bindings"][0]["script"]
    assert "toolbox.get_value('new_name')" in source
    assert "note = 'old_name'" in source


def test_binding_references_remap_inside_duplicated_subtree_payload():
    row = create_item(
        "row",
        {
            "id": "row",
            "name": "row",
            "items": [
                {
                    "kind": "button",
                    "id": "button",
                    "name": "button",
                    "bindings": [
                        {
                            "id": "click",
                            "event": "click",
                            "language": "python",
                            "script": (
                                "toolbox.store_value('inside', 1)"
                            ),
                        }
                    ],
                }
            ],
        }
    )

    changed = rewrite_subtree_references(
        row,
        {"inside": "inside_copy"}
    )

    assert "button" in changed
    assert "inside_copy" in (
        row["items"][0]["bindings"][0]["script"]
    )


def test_shift_click_is_a_normal_binding_modifier():
    item = create_item(
        "button",
        {
            "bindings": [
                {
                    "id": "normal",
                    "event": "click",
                    "mouse_button": "left",
                    "modifiers": [],
                    "language": "python",
                    "script": "normal = True",
                },
                {
                    "id": "shift",
                    "event": "click",
                    "mouse_button": "left",
                    "modifiers": ["shift"],
                    "language": "mel",
                    "script": "polyCube;",
                },
            ],
        }
    )

    normal = matching_bindings(
        item,
        "click",
        mouse_button="left",
        modifiers=[]
    )
    shifted = matching_bindings(
        item,
        "click",
        mouse_button="left",
        modifiers=["shift"]
    )

    assert [entry["id"] for entry in normal] == ["normal"]
    assert [entry["id"] for entry in shifted] == ["shift"]
    assert shifted[0]["language"] == "mel"
    assert "button_mode" not in shifted[0]
