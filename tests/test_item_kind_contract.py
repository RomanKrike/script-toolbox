# -*- coding: utf-8 -*-

from script_toolbox.model import ITEM_TYPES
from script_toolbox.model import create_item


def test_builtin_item_kinds_match_authoritative_registry():
    kinds = ITEM_TYPES.kinds()
    assert "image" in kinds
    assert "column" in kinds

    for kind in kinds:
        assert create_item(kind)["kind"] == kind


def test_removed_toggle_kind_is_not_advertised():
    kinds = ITEM_TYPES.kinds()
    assert "toggle" not in kinds
    assert "toggle_button" in kinds
    assert "toggle_icon" in kinds
