# -*- coding: utf-8 -*-

from script_toolbox.core.completion import CONTEXT_ITEM_ARGUMENT
from script_toolbox.core.completion import CONTEXT_TOOLBOX_MEMBER
from script_toolbox.core.completion import CompletionEngine
from script_toolbox.core.completion import EditorItemsProvider
from script_toolbox.core.completion import SOURCE_EDITOR_ITEM
from script_toolbox.core.completion import SOURCE_TOOLBOX_API
from script_toolbox.core.completion import ScriptToolboxApiProvider
from script_toolbox.core.completion import apply_completion


def sample_items():
    return [
        {
            "kind": "field",
            "name": "width",
            "label": "Width",
            "value": "",
        },
        {
            "kind": "field",
            "name": "height",
            "label": "Height",
            "value": "",
        },
        {
            "kind": "field",
            "name": "output_path",
            "label": "Output Path",
            "value": "",
        },
        {
            "kind": "menu",
            "name": "render_mode",
            "label": "Render Mode",
            "value": "Preview",
        },
        {
            "kind": "button",
            "name": "render",
            "label": "Render",
        },
    ]


class FakeToolbox(object):

    def all_items(self):
        return []

    def find_item(self, key):
        return None

    def get_value(self, key, default=None):
        return default

    def set_value(self, key, value):
        return True

    def field_display_values(self, key):
        return []

    def clear_field(self, key):
        return True


def make_engine(items):
    return CompletionEngine([
        EditorItemsProvider(
            lambda: items
        ),
        ScriptToolboxApiProvider(
            lambda: FakeToolbox()
        ),
    ])


def names(items):
    return [
        item.name
        for item in items
    ]


def test_editor_items_are_available_for_manual_completion():
    items = sample_items()
    engine = make_engine(items)

    _, completions = engine.complete(
        "",
        0,
        manual=True
    )

    assert names(completions) == [
        "height",
        "output_path",
        "render",
        "render_mode",
        "width",
    ]
    assert all(
        item.source == SOURCE_EDITOR_ITEM
        for item in completions
    )


def test_completion_filters_case_insensitive_prefix():
    engine = make_engine(
        sample_items()
    )

    _, completions = engine.complete(
        "REN",
        3,
        manual=True
    )

    assert names(completions) == [
        "render",
        "render_mode",
    ]


def test_editor_item_source_updates_after_add_delete_and_rename():
    items = sample_items()
    engine = make_engine(items)

    items.append({
        "kind": "string",
        "name": "camera",
        "label": "Camera",
        "value": "",
    })
    assert "camera" in names(
        engine.complete(
            "",
            0,
            manual=True
        )[1]
    )

    items[0]["name"] = "render_width"
    current = names(
        engine.complete(
            "",
            0,
            manual=True
        )[1]
    )
    assert "render_width" in current
    assert "width" not in current

    del items[1]
    current = names(
        engine.complete(
            "",
            0,
            manual=True
        )[1]
    )
    assert "height" not in current


def test_get_value_context_recognizes_item_argument():
    engine = make_engine(
        sample_items()
    )
    code = 'toolbox.get_value("ren'

    context, completions = engine.complete(
        code,
        len(code),
        manual=False
    )

    assert context.kind == CONTEXT_ITEM_ARGUMENT
    assert context.api_name == "get_value"
    assert context.prefix == "ren"
    assert names(completions) == [
        "render_mode",
    ]


def test_get_value_only_suggests_value_items():
    engine = make_engine(
        sample_items()
    )
    code = 'toolbox.get_value("'

    _, completions = engine.complete(
        code,
        len(code),
        manual=False
    )

    assert "render_mode" in names(completions)
    assert "render" not in names(completions)


def test_field_api_context_only_suggests_fields():
    engine = make_engine(
        sample_items()
    )
    code = 'toolbox.clear_field("'

    _, completions = engine.complete(
        code,
        len(code),
        manual=False
    )

    assert names(completions) == [
        "height",
        "output_path",
        "width",
    ]


def test_item_completion_inserts_technical_name():
    engine = make_engine(
        sample_items()
    )
    code = 'toolbox.get_value("ren'
    context, completions = engine.complete(
        code,
        len(code),
        manual=False
    )

    result, cursor = apply_completion(
        code,
        len(code),
        context,
        completions[0]
    )

    assert result == 'toolbox.get_value("render_mode'
    assert cursor == len(result)


def test_toolbox_member_completion_uses_real_available_api():
    engine = make_engine(
        sample_items()
    )
    code = "toolbox.get_"

    context, completions = engine.complete(
        code,
        len(code),
        manual=False
    )

    assert context.kind == CONTEXT_TOOLBOX_MEMBER
    assert names(completions) == [
        "get_value",
    ]
    assert completions[0].source == SOURCE_TOOLBOX_API
    assert completions[0].display_text == "get_value(key, default=None)"


def test_api_completion_inserts_snippet_and_moves_cursor_to_item_argument():
    engine = make_engine(
        sample_items()
    )
    code = "toolbox.ge"
    context, completions = engine.complete(
        code,
        len(code),
        manual=False
    )
    completion = [
        item
        for item in completions
        if item.name == "get_value"
    ][0]

    result, cursor = apply_completion(
        code,
        len(code),
        context,
        completion
    )

    assert result == 'toolbox.get_value("")'
    assert result[:cursor] == 'toolbox.get_value("'


def test_no_matching_completion_returns_empty_list():
    engine = make_engine(
        sample_items()
    )

    _, completions = engine.complete(
        "does_not_exist",
        len("does_not_exist"),
        manual=False
    )

    assert completions == []
