# -*- coding: utf-8 -*-

from script_toolbox.core import event_bindings
from script_toolbox.core.event_bindings import dispatch_item_event
from script_toolbox.core.references import rewrite_item_references
from script_toolbox.model.bindings import binding_display_name
from script_toolbox.model.bindings import binding_events
from script_toolbox.model.bindings import make_binding
from script_toolbox.model.bindings import matching_bindings
from script_toolbox.model.items import create_item


def test_layout_bindings_are_internal_only_for_now():
    assert binding_events("folder") == ()
    assert binding_events("row") == ()
    assert binding_events("column") == ()
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
                    binding_id="plain"
                ),
                make_binding(
                    "click",
                    language="mel",
                    script="polyCube;",
                    modifiers=["ctrl", "alt"],
                    binding_id="combo"
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
                    binding_id="python"
                ),
                make_binding(
                    "double_click",
                    language="mel",
                    script="polyCube;",
                    binding_id="mel"
                ),
            ],
        }
    )

    assert item["bindings"][0]["language"] == "python"
    assert item["bindings"][1]["language"] == "mel"
    assert all(
        "button_mode" not in binding
        for binding in item["bindings"]
    )


def test_toggle_button_has_native_state_trigger_and_can_add_script_trigger():
    item = create_item(
        "toggle_button",
        {
            "bindings": [
                make_binding(
                    "click",
                    handler="state_toggle",
                    binding_id="toggle"
                ),
                make_binding(
                    "click",
                    script="after_toggle = True",
                    binding_id="script"
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

    assert [entry["id"] for entry in matched] == [
        "toggle",
        "script",
    ]
    assert matched[0]["handler"] == "state_toggle"
    assert matched[1]["handler"] == "script"


def test_state_toggle_handler_is_not_valid_for_plain_button():
    item = create_item(
        "button",
        {
            "bindings": [
                make_binding(
                    "click",
                    handler="state_toggle",
                    binding_id="invalid"
                )
            ],
        }
    )

    assert item["bindings"][0]["handler"] == "script"


def test_reference_rewrite_only_touches_python_binding_scripts():
    item = create_item(
        "button",
        {
            "bindings": [
                make_binding(
                    "click",
                    language="python",
                    script="toolbox.get_value('old_name')",
                    binding_id="python"
                ),
                make_binding(
                    "double_click",
                    language="mel",
                    script='python("toolbox.get_value(\\"old_name\\")");',
                    binding_id="mel"
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
                    binding_id="mel"
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
