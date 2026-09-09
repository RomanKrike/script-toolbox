# -*- coding: utf-8 -*-

from script_toolbox.constants import CONFIG_VERSION
from script_toolbox.core import event_bindings
from script_toolbox.core.event_bindings import dispatch_item_event
from script_toolbox.core.migrations import migrate_document
from script_toolbox.core.references import rewrite_item_references
from script_toolbox.model.bindings import binding_display_name
from script_toolbox.model.bindings import binding_events
from script_toolbox.model.bindings import make_binding
from script_toolbox.model.bindings import matching_bindings
from script_toolbox.model.items import create_item


def test_layout_bindings_are_internal_only_for_now():
    assert binding_events("folder") == ()
    assert binding_events("row") == ()
    assert binding_events("separator") == ()
    assert binding_events("folder", include_internal=True) == (
        "opened",
        "closed",
    )


def test_mouse_binding_display_name_includes_modifiers_and_button():
    binding = make_binding(
        "double_click",
        mouse_button="right",
        modifiers=["shift", "ctrl"]
    )

    assert binding_display_name(binding) == (
        "Ctrl + Shift + Right + Double Click"
    )


def test_modifier_matching_is_exact_by_default():
    item = create_item(
        "button",
        {
            "bindings": [
                make_binding(
                    "click",
                    script="plain = True",
                    modifiers=[],
                    binding_id="plain",
                    button_mode="action"
                ),
                make_binding(
                    "click",
                    language="mel",
                    script="polyCube;",
                    modifiers=["ctrl", "alt"],
                    binding_id="combo",
                    button_mode="action"
                ),
            ],
        }
    )

    assert [
        entry["id"]
        for entry in matching_bindings(
            item,
            "click",
            modifiers=[]
        )
    ] == ["plain"]
    assert [
        entry["id"]
        for entry in matching_bindings(
            item,
            "click",
            modifiers=["alt", "ctrl"]
        )
    ] == ["combo"]
    assert matching_bindings(
        item,
        "click",
        modifiers=["shift"]
    ) == []


def test_button_can_mix_python_and_mel_per_trigger():
    item = create_item(
        "button",
        {
            "bindings": [
                make_binding(
                    "click",
                    language="python",
                    script="python_call = True",
                    binding_id="python",
                    button_mode="action"
                ),
                make_binding(
                    "double_click",
                    language="mel",
                    script="polyCube;",
                    binding_id="mel",
                    button_mode="action"
                ),
            ],
        }
    )

    assert "language" not in item
    assert item["bindings"][0]["language"] == "python"
    assert item["bindings"][1]["language"] == "mel"


def test_toggle_button_keeps_state_toggle_binding_separate_from_action_mode():
    item = create_item(
        "toggle_button",
        {
            "bindings": [
                make_binding(
                    "click",
                    handler="state_toggle",
                    button_mode="state",
                    binding_id="toggle"
                ),
                make_binding(
                    "click",
                    script="should_not_run = True",
                    button_mode="action",
                    binding_id="legacy_action"
                ),
            ],
        }
    )

    matched = matching_bindings(
        item,
        "click",
        mouse_button="left",
        modifiers=[]
    )

    assert [entry["id"] for entry in matched] == ["toggle"]
    assert matched[0]["handler"] == "state_toggle"


def test_schema17_migrates_click_shift_callbacks_and_folder_events():
    source = {
        "version": 17,
        "sections": [
            {
                "kind": "folder",
                "id": "root",
                "name": "root",
                "callbacks": {
                    "on_open": "print('open')",
                    "on_close": "print('close')",
                },
                "items": [
                    {
                        "kind": "button",
                        "id": "run",
                        "name": "run",
                        "mode": "action",
                        "language": "mel",
                        "click_script": "polyCube;",
                        "shift_script": "polySphere;",
                        "callbacks": {
                            "on_click": "toolbox.get_value('value')",
                        },
                    },
                    {
                        "kind": "integer",
                        "id": "value",
                        "name": "value",
                        "callbacks": {
                            "on_change": "print(value)",
                        },
                    },
                ],
            }
        ],
    }

    migrated = migrate_document(source)
    folder = migrated["sections"][0]
    button = folder["items"][0]
    value = folder["items"][1]

    assert migrated["version"] == CONFIG_VERSION
    assert "callbacks" not in folder
    assert "callbacks" not in button
    assert "language" not in button
    assert "click_script" not in button
    assert "shift_script" not in button

    assert [entry["event"] for entry in folder["bindings"]] == [
        "opened",
        "closed",
    ]
    assert binding_events("folder") == ()

    mel_bindings = [
        entry
        for entry in button["bindings"]
        if entry.get("language") == "mel"
    ]
    assert len(mel_bindings) == 2
    assert mel_bindings[0]["script"] == "polyCube;"
    assert mel_bindings[1]["modifiers"] == ["shift"]

    callback_binding = [
        entry
        for entry in button["bindings"]
        if entry.get("language") == "python"
    ][0]
    assert callback_binding["event"] == "click"
    assert callback_binding["modifier_policy"] == "any"

    assert value["bindings"][0]["event"] == "value_changed"
    assert value["bindings"][0]["script"] == "print(value)"


def test_schema17_state_button_becomes_toggle_and_keeps_native_transitions():
    source = {
        "version": 17,
        "sections": [
            {
                "kind": "folder",
                "name": "root",
                "items": [
                    {
                        "kind": "button",
                        "id": "state",
                        "name": "state",
                        "mode": "state",
                        "language": "mel",
                        "state_get_script": "state = True",
                        "state_on_script": "showHidden -a;",
                        "state_off_script": "hide;",
                    }
                ],
            }
        ],
    }

    migrated = migrate_document(source)
    item = migrated["sections"][0]["items"][0]

    assert item["kind"] == "toggle_button"
    assert item["state_source"] == "script"
    assert item["state_get_language"] == "python"
    assert item["state_on_language"] == "mel"
    assert item["state_off_language"] == "mel"
    assert item["bindings"][0]["handler"] == "state_toggle"


def test_reference_rewrite_only_touches_python_binding_scripts():
    item = create_item(
        "button",
        {
            "bindings": [
                make_binding(
                    "click",
                    language="python",
                    script="toolbox.get_value('old_name')",
                    binding_id="python",
                    button_mode="action"
                ),
                make_binding(
                    "double_click",
                    language="mel",
                    script='python("toolbox.get_value(\\"old_name\\")");',
                    binding_id="mel",
                    button_mode="action"
                ),
            ],
        }
    )

    assert rewrite_item_references(
        item,
        {"old_name": "new_name"}
    ) is True

    assert "new_name" in item["bindings"][0]["script"]
    assert "old_name" in item["bindings"][1]["script"]


def test_python_binding_receives_event_namespace():
    item = create_item(
        "string",
        {
            "id": "name",
            "name": "name",
            "value": "new",
            "bindings": [
                make_binding(
                    "value_changed",
                    language="python",
                    script=(
                        "toolbox.record = (value, old_value, event['name'], "
                        "item['name'])"
                    ),
                    binding_id="changed"
                )
            ],
        }
    )

    class Toolbox(object):
        def __init__(self):
            self.record = None
            self._binding_guard = set()

        def find_item(self, key):
            return item

    toolbox = Toolbox()
    results = dispatch_item_event(
        toolbox,
        item,
        "value_changed",
        value="new",
        old_value="old",
        parent=None
    )

    assert len(results) == 1
    assert results[0].success is True
    assert toolbox.record == (
        "new",
        "old",
        "value_changed",
        "name",
    )


def test_native_binding_uses_its_own_language(monkeypatch):
    item = create_item(
        "button",
        {
            "bindings": [
                make_binding(
                    "click",
                    language="mel",
                    script="polyCube;",
                    binding_id="mel",
                    button_mode="action"
                )
            ],
        }
    )
    captured = {}

    class Result(object):
        success = True

    def fake_execute(
        code,
        language="python",
        toolbox=None,
        parent=None,
        extra_namespace=None,
        context="",
        notify=True
    ):
        captured["code"] = code
        captured["language"] = language
        captured["context"] = context
        return Result()

    monkeypatch.setattr(
        event_bindings,
        "execute_script_result",
        fake_execute
    )

    class Toolbox(object):
        _binding_guard = set()

        def find_item(self, key):
            return item

    results = dispatch_item_event(
        Toolbox(),
        item,
        "click",
        mouse_button="left",
        modifiers=[]
    )

    assert results[0].success is True
    assert captured["language"] == "mel"
    assert captured["code"] == "polyCube;"
    assert "binding:" in captured["context"]
