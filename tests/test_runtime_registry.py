# -*- coding: utf-8 -*-

import pytest

from script_toolbox.core.runtime_registry import RuntimeRendererRegistry


def test_registry_registers_and_renders_normalized_kind():
    registry = RuntimeRendererRegistry()
    calls = []

    def renderer(owner, item, compact=False):
        calls.append((owner, item["id"], compact))
        return "rendered"

    registry.register(
        " Button ",
        renderer
    )

    owner = object()
    result = registry.render(
        owner,
        {
            "kind": "BUTTON",
            "id": "button_a",
        },
        compact=True
    )

    assert result == "rendered"
    assert calls == [(owner, "button_a", True)]
    assert registry.has("button") is True
    assert registry.renderer_for(" BUTTON ") is renderer


def test_registry_rejects_empty_noncallable_and_duplicate_entries():
    registry = RuntimeRendererRegistry()

    with pytest.raises(ValueError):
        registry.register("", lambda owner, item, compact=False: None)

    with pytest.raises(TypeError):
        registry.register("button", object())

    first = lambda owner, item, compact=False: "first"
    second = lambda owner, item, compact=False: "second"

    registry.register("button", first)

    with pytest.raises(ValueError):
        registry.register("button", second)

    registry.register(
        "button",
        second,
        replace=True
    )
    assert registry.renderer_for("button") is second


def test_registry_unknown_and_invalid_items_are_noop():
    registry = RuntimeRendererRegistry()

    assert registry.render(None, None) is None
    assert registry.render(None, []) is None
    assert registry.render(None, {"kind": "missing"}) is None


def test_registry_unregister_and_sorted_kinds():
    registry = RuntimeRendererRegistry()
    renderer = lambda owner, item, compact=False: None

    registry.register("string", renderer)
    registry.register("button", renderer)
    registry.register("float", renderer)

    assert registry.kinds() == (
        "button",
        "float",
        "string",
    )
    assert registry.unregister(" FLOAT ") is renderer
    assert registry.unregister("float") is None
    assert registry.has("float") is False
