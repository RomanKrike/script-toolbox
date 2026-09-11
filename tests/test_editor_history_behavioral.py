# -*- coding: utf-8 -*-

from script_toolbox.constants import CONFIG_VERSION
from script_toolbox.core.editor_commands import CommandHistory
from script_toolbox.core.editor_commands import DocumentCapture
from script_toolbox.core.editor_commands import ItemStateCommand
from script_toolbox.core.editor_commands import build_document_delta
from script_toolbox.core.editor_document import EditorDocumentController


def _button():
    return {
        "kind": "button",
        "id": "button",
        "name": "button",
        "label": "Button",
        "language": "python",
        "click_script": "",
    }


def _document():
    return {
        "version": CONFIG_VERSION,
        "sections": [{
            "kind": "folder",
            "id": "root",
            "name": "root",
            "label": "Root",
            "items": [],
        }],
    }


def test_create_edit_undo_redo_branch_and_noop_history_flow():
    controller = EditorDocumentController(_document())
    history = CommandHistory(controller)

    capture = DocumentCapture(controller)
    controller.document["sections"][0]["items"].append(_button())
    controller.rebuild_index()
    history.push_applied(
        build_document_delta(controller, capture, label="Create Parameter")
    )

    button = controller.find_by_id("button")
    before = controller.item_state(button)
    button["label"] = "Changed"
    history.push_applied(
        ItemStateCommand(
            "button",
            before,
            controller.item_state(button),
            label="Edit Parameter"
        )
    )

    history.undo()
    assert controller.find_by_id("button")["label"] == "Button"
    history.undo()
    assert controller.find_by_id("button") is None
    history.redo()
    history.redo()
    assert controller.find_by_id("button")["label"] == "Changed"

    history.undo()
    assert history.can_redo is True
    button = controller.find_by_id("button")
    before = controller.item_state(button)
    button["label"] = "Branch"
    history.push_applied(
        ItemStateCommand("button", before, controller.item_state(button))
    )
    assert history.can_redo is False

    unchanged = DocumentCapture(controller)
    assert build_document_delta(controller, unchanged) is None
    undo_count = len(history.undo_stack)
    assert history.push_applied(None) is False
    assert len(history.undo_stack) == undo_count
