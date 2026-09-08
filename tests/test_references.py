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


def test_rewrite_item_references_skips_mel_button_action_scripts():
    item = {
        "kind": "button",
        "id": "button_a",
        "name": "button_a",
        "language": "mel",
        "click_script": 'print("toolbox.get_value(\\\"source_mesh\\\")")',
        "shift_script": 'print("toolbox.set_value(\\\"source_mesh\\\", 1)")',
        "state_get_script": "toolbox.get_value('source_mesh') is not None",
    }

    changed = rewrite_item_references(
        item,
        {"source_mesh": "source_mesh_2"}
    )

    assert changed is True
    assert "source_mesh_2" not in item["click_script"]
    assert "source_mesh_2" not in item["shift_script"]
    assert item["state_get_script"] == (
        "toolbox.get_value('source_mesh_2') is not None"
    )


def test_rewrite_item_references_updates_on_change_python_script():
    item = {
        "kind": "string",
        "id": "string_a",
        "name": "string_a",
        "on_change_script": "toolbox.set_value('target', value)",
    }

    changed = rewrite_item_references(
        item,
        {"target": "target_2"}
    )

    assert changed is True
    assert item["on_change_script"] == (
        "toolbox.set_value('target_2', value)"
    )
