# -*- coding: utf-8 -*-

import os


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


def _source(*parts):
    with open(os.path.join(ROOT, *parts), "r") as handle:
        return handle.read()


def test_binding_inspector_uses_item_capability_for_state_toggle():
    source = _source(
        "scripts",
        "script_toolbox",
        "ui",
        "properties",
        "bindings.py",
    )

    assert "STATE_TOGGLE_KINDS" not in source
    assert "register_builtin_items" in source
    assert "ITEM_TYPES.get" in source
    assert '_item_has_capability(kind, "state_toggle")' in source


def test_model_bindings_remains_free_of_legacy_state_toggle_kind_list():
    source = _source(
        "scripts",
        "script_toolbox",
        "model",
        "bindings.py",
    )

    assert "STATE_TOGGLE_KINDS" not in source
    assert 'has_capability("state_toggle")' in source
