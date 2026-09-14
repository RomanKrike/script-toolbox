# -*- coding: utf-8 -*-

from script_toolbox.core.references import rewrite_item_references
from script_toolbox.core.references import rewrite_python_references


def test_rewrite_python_references_updates_managed_literal_arguments_only():
    source = "\n".join([
        "value = toolbox.get_value('source_mesh')",
        'toolbox.set_value("source_mesh", value)',
        "toolbox.add_to_field('source_mesh', ['pCube1'])",
        "plain = 'source_mesh'",
        "# toolbox.get_value('source_mesh')",
        "other.toolbox.get_value('source_mesh')",
        "toolbox.unknown_method('source_mesh')",
        "key = 'source_mesh'",
        "toolbox.get_value(key)",
    ])

    rewritten = rewrite_python_references(
        source,
        {"source_mesh": "source_mesh_2"}
    )

    assert "toolbox.get_value('source_mesh_2')" in rewritten
    assert 'toolbox.set_value("source_mesh_2", value)' in rewritten
    assert "toolbox.add_to_field('source_mesh_2', ['pCube1'])" in rewritten
    assert "plain = 'source_mesh'" in rewritten
    assert "# toolbox.get_value('source_mesh')" in rewritten
    assert "other.toolbox.get_value('source_mesh')" in rewritten
    assert "toolbox.unknown_method('source_mesh')" in rewritten
    assert "key = 'source_mesh'" in rewritten
    assert "toolbox.get_value(key)" in rewritten


def test_rewrite_python_references_can_remap_stable_ids():
    source = "value = toolbox.get_value('field_old_id')"

    rewritten = rewrite_python_references(
        source,
        {"field_old_id": "field_new_id"}
    )

    assert rewritten == "value = toolbox.get_value('field_new_id')"


def test_rewrite_item_references_uses_props_language_metadata():
    item = {
        "kind": "toggle_button",
        "id": "toggle_a",
        "name": "toggle_a",
        "ui": {"label": "Toggle"},
        "props": {
            "state_get_script": "toolbox.get_value('source_mesh') is not None",
            "state_get_language": "python",
            "state_on_script": 'print("toolbox.get_value(\\\"source_mesh\\\")")',
            "state_on_language": "mel",
        },
        "bindings": [],
    }

    changed = rewrite_item_references(
        item,
        {"source_mesh": "source_mesh_2"}
    )

    assert changed is True
    assert item["props"]["state_get_script"] == (
        "toolbox.get_value('source_mesh_2') is not None"
    )
    assert "source_mesh_2" not in item["props"]["state_on_script"]


def test_rewrite_item_references_updates_python_script_props_generically():
    item = {
        "kind": "toggle_icon",
        "id": "toggle_icon_a",
        "name": "toggle_icon_a",
        "ui": {"label": "Toggle Icon"},
        "props": {
            "state_off_script": "toolbox.set_value('target', value)",
            "state_off_language": "python",
        },
        "bindings": [],
    }

    changed = rewrite_item_references(
        item,
        {"target": "target_2"}
    )

    assert changed is True
    assert item["props"]["state_off_script"] == (
        "toolbox.set_value('target_2', value)"
    )
