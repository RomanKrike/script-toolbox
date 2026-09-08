# -*- coding: utf-8 -*-

import copy

from script_toolbox.core.editor_commands import CommandHistory
from script_toolbox.core.editor_commands import DocumentCapture
from script_toolbox.core.editor_commands import ItemStateCommand
from script_toolbox.core.editor_commands import build_document_delta
from script_toolbox.core.editor_document import EditorDocumentController


def _item(item_id, name, label=None):
    return {
        "kind": "button",
        "id": item_id,
        "name": name,
        "label": label or name.title(),
        "language": "python",
        "click_script": "print('{0}')".format(name),
    }


def _document():
    return {
        "version": 16,
        "sections": [
            {
                "kind": "folder",
                "id": "folder_main",
                "name": "main",
                "label": "Main",
                "folder_type": "collapsible",
                "items": [
                    _item("button_a", "a"),
                    _item("button_b", "b"),
                ],
            }
        ],
    }


def _child_ids(controller):
    folder = controller.find_by_id("folder_main")
    return [item["id"] for item in folder["items"]]


def test_item_state_command_undo_redo_changes_only_one_item():
    controller = EditorDocumentController(_document())
    history = CommandHistory(controller)
    item = controller.find_by_id("button_a")
    before = controller.item_state(item)

    item["label"] = "Changed"
    after = controller.item_state(item)
    command = ItemStateCommand(
        "button_a",
        before,
        after
    )
    history.push_applied(command)

    history.undo()
    assert controller.find_by_id("button_a")["label"] == "A"
    assert controller.find_by_id("button_b")["label"] == "B"

    history.redo()
    assert controller.find_by_id("button_a")["label"] == "Changed"
    assert controller.find_by_id("button_b")["label"] == "B"


def test_structural_reorder_uses_topology_and_round_trips():
    controller = EditorDocumentController(_document())
    capture = DocumentCapture(controller)
    folder = controller.find_by_id("folder_main")
    folder["items"] = list(reversed(folder["items"]))
    controller.rebuild_index()

    command = build_document_delta(
        controller,
        capture,
        label="Move Parameter"
    )
    history = CommandHistory(controller)
    history.push_applied(command)

    assert _child_ids(controller) == ["button_b", "button_a"]
    assert command.before_missing == {}
    assert command.after_missing == {}
    assert command.before_states == {}

    history.undo()
    assert _child_ids(controller) == ["button_a", "button_b"]

    history.redo()
    assert _child_ids(controller) == ["button_b", "button_a"]


def test_insert_command_stores_only_added_payload_not_unchanged_items():
    controller = EditorDocumentController(_document())
    capture = DocumentCapture(controller)
    folder = controller.find_by_id("folder_main")
    folder["items"].append(_item("button_c", "c"))
    controller.rebuild_index()

    command = build_document_delta(controller, capture)

    assert set(command.after_missing.keys()) == set(["button_c"])
    assert command.before_missing == {}
    assert "button_a" not in command.after_missing
    assert "button_b" not in command.after_missing
    assert command.before_states == {}

    history = CommandHistory(controller)
    history.push_applied(command)
    history.undo()
    assert _child_ids(controller) == ["button_a", "button_b"]
    assert controller.find_by_id("button_c") is None

    history.redo()
    assert _child_ids(controller) == ["button_a", "button_b", "button_c"]
    assert controller.find_by_id("button_c")["name"] == "c"


def test_delete_command_preserves_only_removed_subtree_for_undo():
    controller = EditorDocumentController(_document())
    capture = DocumentCapture(controller)
    folder = controller.find_by_id("folder_main")
    folder["items"].pop(0)
    controller.rebuild_index()

    command = build_document_delta(controller, capture)

    assert set(command.before_missing.keys()) == set(["button_a"])
    assert command.after_missing == {}

    history = CommandHistory(controller)
    history.push_applied(command)
    history.undo()
    assert _child_ids(controller) == ["button_a", "button_b"]

    history.redo()
    assert _child_ids(controller) == ["button_b"]
    assert controller.find_by_id("button_a") is None


def test_replace_document_delta_restores_old_and_new_documents():
    controller = EditorDocumentController(_document())
    capture = DocumentCapture(controller)
    replacement = {
        "version": 16,
        "profile": "replacement",
        "sections": [
            {
                "kind": "folder",
                "id": "folder_other",
                "name": "other",
                "label": "Other",
                "items": [
                    _item("button_x", "x")
                ],
            }
        ],
    }
    controller.replace(replacement)

    command = build_document_delta(
        controller,
        capture,
        label="Import Toolbox"
    )
    history = CommandHistory(controller)
    history.push_applied(command)

    assert controller.find_by_id("button_x") is not None
    assert controller.document["profile"] == "replacement"

    history.undo()
    assert controller.find_by_id("button_a") is not None
    assert controller.find_by_id("button_x") is None
    assert "profile" not in controller.document

    history.redo()
    assert controller.find_by_id("button_x") is not None
    assert controller.find_by_id("button_a") is None
    assert controller.document["profile"] == "replacement"


def test_common_item_payload_change_is_stored_without_children_snapshot():
    controller = EditorDocumentController(_document())
    capture = DocumentCapture(controller)
    item = controller.find_by_id("button_a")
    item["click_script"] = "print('updated')"

    command = build_document_delta(controller, capture)

    assert set(command.before_states.keys()) == set(["button_a"])
    assert set(command.after_states.keys()) == set(["button_a"])
    assert command.before_missing == {}
    assert command.after_missing == {}

    history = CommandHistory(controller)
    history.push_applied(command)
    history.undo()
    assert controller.find_by_id("button_a")["click_script"] == "print('a')"
    history.redo()
    assert controller.find_by_id("button_a")["click_script"] == "print('updated')"


def test_document_capture_ignores_detached_cache_entries():
    controller = EditorDocumentController(_document())
    detached = _item("button_detached", "detached")
    controller.cache_subtree(detached)

    capture = DocumentCapture(controller)

    assert "button_detached" not in capture.item_refs
    assert "button_detached" not in capture.item_states


def test_history_limit_and_redo_invalidation():
    controller = EditorDocumentController(_document())
    history = CommandHistory(controller, limit=2)

    for index in range(3):
        item = controller.find_by_id("button_a")
        before = controller.item_state(item)
        item["label"] = "Value {0}".format(index)
        after = controller.item_state(item)
        history.push_applied(
            ItemStateCommand(
                "button_a",
                before,
                after
            )
        )

    assert len(history.undo_stack) == 2
    history.undo()
    assert history.can_redo is True

    item = controller.find_by_id("button_a")
    before = controller.item_state(item)
    item["label"] = "Branch"
    history.push_applied(
        ItemStateCommand(
            "button_a",
            before,
            controller.item_state(item)
        )
    )

    assert history.can_redo is False


def test_command_payloads_are_defensive_copies():
    controller = EditorDocumentController(_document())
    item = controller.find_by_id("button_a")
    before = controller.item_state(item)
    item["label"] = "After"
    after = controller.item_state(item)
    command = ItemStateCommand("button_a", before, after)

    before["label"] = "Corrupted"
    after["label"] = "Corrupted"

    command.undo(controller)
    assert controller.find_by_id("button_a")["label"] == "A"
    command.redo(controller)
    assert controller.find_by_id("button_a")["label"] == "After"
