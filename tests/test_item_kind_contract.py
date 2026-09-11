# -*- coding: utf-8 -*-

from script_toolbox.constants import ITEM_KINDS
from script_toolbox.model import create_item
from script_toolbox.model import items as items_module


def test_builtin_item_kinds_match_model_factory_registry():
    assert set(ITEM_KINDS) == set(items_module._FACTORIES)

    for kind in ITEM_KINDS:
        assert create_item(kind)["kind"] == kind


def test_removed_toggle_kind_is_not_advertised():
    assert "toggle" not in ITEM_KINDS
    assert "toggle_button" in ITEM_KINDS
    assert "toggle_icon" in ITEM_KINDS
