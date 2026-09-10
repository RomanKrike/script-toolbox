# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)
sys.path.insert(
    0,
    os.path.join(
        ROOT,
        "scripts"
    )
)

from script_toolbox.constants import CONFIG_VERSION
from script_toolbox.core import config
from script_toolbox.core.config_store import ConfigStore
from script_toolbox.core.editor_commands import CommandHistory
from script_toolbox.core.editor_commands import ItemStateCommand
from script_toolbox.core.editor_document import EditorDocumentController
from script_toolbox.core.runtime_registry import RuntimeRendererRegistry
from script_toolbox.core.state_refresh import StateRefreshQueue


def main():
    folder = tempfile.mkdtemp(
        prefix="script_toolbox_config_py2_"
    )
    path = os.path.join(
        folder,
        "toolbox.json"
    )

    try:
        config.save_config({}, path=path)
        document = config.load_config(path=path)
        assert document["version"] == CONFIG_VERSION
        assert document["sections"]
        assert os.path.isfile(path)

        store = ConfigStore(document=document, path=path)
        store.mark_dirty()
        store.flush()

        assert store.dirty is False
        assert store.write_count == 1
        assert os.path.isfile(config.backup_path(path, 1))

        refresh_queue = StateRefreshQueue()
        assert refresh_queue.request() is True
        assert refresh_queue.request() is False
        assert refresh_queue.consume() is True
        assert refresh_queue.pending is False

        editor_document = {
            "version": CONFIG_VERSION,
            "sections": [
                {
                    "kind": "folder",
                    "id": "root",
                    "name": "root",
                    "label": "Root",
                    "items": [
                        {
                            "kind": "string",
                            "id": "value",
                            "name": "value",
                            "label": "Value",
                            "value": "test",
                        }
                    ],
                }
            ],
        }
        controller = EditorDocumentController(editor_document)
        assert controller.find_by_id("value")["value"] == "test"

        clone = controller.clone_subtree(
            controller.document["sections"][0]
        )
        assert clone["id"] != "root"
        assert clone["items"][0]["id"] != "value"

        value_item = controller.find_by_id("value")
        before = controller.item_state(value_item)
        value_item["value"] = "changed"
        after = controller.item_state(value_item)
        history = CommandHistory(controller)
        history.push_applied(
            ItemStateCommand(
                "value",
                before,
                after
            )
        )
        history.undo()
        assert controller.find_by_id("value")["value"] == "test"
        history.redo()
        assert controller.find_by_id("value")["value"] == "changed"

        registry = RuntimeRendererRegistry()

        def render(owner, item, compact=False):
            return (item["id"], bool(compact))

        registry.register("button", render)
        assert registry.render(
            None,
            {
                "kind": "BUTTON",
                "id": "button_a",
            },
            compact=True
        ) == ("button_a", True)
    finally:
        shutil.rmtree(folder)


if __name__ == "__main__":
    main()
