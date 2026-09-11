# -*- coding: utf-8 -*-

from script_toolbox.constants import CONFIG_VERSION
from script_toolbox.core.editor_document import EditorDocumentController
from script_toolbox.core.references import rewrite_document_references_result
from script_toolbox.core.references import rewrite_python_references_result


def _document(items=None):
    return {
        "version": CONFIG_VERSION,
        "sections": [{
            "kind": "folder",
            "id": "root",
            "name": "root",
            "label": "Root",
            "items": list(items or []),
        }],
    }


def _button(item_id, name, script):
    return {
        "kind": "button",
        "id": item_id,
        "name": name,
        "label": name.title(),
        "language": "python",
        "click_script": script,
    }


def test_reference_rewrite_reports_alias_dynamic_and_computed_risks_only():
    source = "\n".join([
        "toolbox.get_value('old')",
        "toolbox.set_value('old', 1)",
        "tb = toolbox",
        "tb.get_value('old')",
        "name = 'old'",
        "toolbox.get_value(name)",
        "toolbox.get_value('o' + 'ld')",
        "# toolbox.get_value('old')",
        "plain = 'old'",
    ])

    result = rewrite_python_references_result(source, {"old": "new"})

    assert "toolbox.get_value('new')" in result["source"]
    assert "toolbox.set_value('new', 1)" in result["source"]
    assert [entry["kind"] for entry in result["unresolved"]] == [
        "alias",
        "dynamic_name",
        "computed",
    ]
    assert "plain = 'old'" in result["source"]
    assert "# toolbox.get_value('old')" in result["source"]


def test_reference_report_identifies_affected_items():
    document = _document([
        _button("reader", "reader", "tb = toolbox\ntb.get_value('old')"),
        _button("safe", "safe", "toolbox.get_value('old')"),
    ])

    result = rewrite_document_references_result(document, {"old": "new"})

    assert result["changed_ids"] == set(["safe"])
    assert [entry["id"] for entry in result["unresolved_items"]] == ["reader"]


def test_duplicate_subtree_remaps_internal_links_and_reports_alias():
    source = {
        "kind": "folder",
        "id": "group",
        "name": "group",
        "label": "Group",
        "items": [
            {
                "kind": "string",
                "id": "source_id",
                "name": "source_value",
                "label": "Source",
                "value": "x",
            },
            _button(
                "reader_id",
                "reader",
                "\n".join([
                    "toolbox.get_value('source_value')",
                    "toolbox.get_value('source_id')",
                    "tb = toolbox",
                    "tb.get_value('source_value')",
                ])
            ),
        ],
    }
    controller = EditorDocumentController(_document([source]))

    clone, result = controller.clone_subtree(
        controller.find_by_id("group"),
        return_result=True
    )

    cloned_source = clone["items"][0]
    script = clone["items"][1]["click_script"]
    assert "toolbox.get_value('{0}')".format(cloned_source["name"]) in script
    assert "toolbox.get_value('{0}')".format(cloned_source["id"]) in script
    assert "tb.get_value('source_value')" in script
    assert result["unresolved_items"][0]["references"][0]["kind"] == "alias"


def test_rename_rewrites_supported_reference_and_reports_unresolved_alias():
    target = {
        "kind": "string",
        "id": "target",
        "name": "old",
        "label": "Target",
        "value": "",
    }
    reader = _button(
        "reader",
        "reader",
        "toolbox.get_value('old')\ntb = toolbox\ntb.get_value('old')"
    )
    controller = EditorDocumentController(_document([target, reader]))
    controller.find_by_id("target")["name"] = "new"

    result = controller.rename_item_references_result("target", "old", "new")

    assert result["changed_ids"] == set(["reader"])
    assert len(result["unresolved_items"]) == 1
    script = controller.find_by_id("reader")["click_script"]
    assert "toolbox.get_value('new')" in script
    assert "tb.get_value('old')" in script
