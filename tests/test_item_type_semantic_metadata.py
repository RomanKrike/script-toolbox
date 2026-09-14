# -*- coding: utf-8 -*-

import pytest

from script_toolbox.constants import CONFIG_VERSION
from script_toolbox.model import ITEM_TYPES
from script_toolbox.model import ItemTypeDefinition
from script_toolbox.model import LayoutSpec
from script_toolbox.model import SectionSpec
from script_toolbox.model import create_item
from script_toolbox.model import normalize_document
from script_toolbox.model import register_item_type
from script_toolbox.model.fields import BoolField
from script_toolbox.model.fields import ChoiceField
from script_toolbox.model.fields import FieldValidationError
from script_toolbox.model.fields import IntField


def test_synthetic_flow_layout_uses_explicit_semantics_with_custom_prop_names():
    kind = "flow_test_layout"
    ITEM_TYPES.unregister(kind)
    definition = ItemTypeDefinition(
        kind=kind,
        title="Flow Test Layout",
        category="Layout",
        fields={
            "gap": IntField(default=3, minimum=0, maximum=20),
            "flow_policy": ChoiceField(
                ("start", "center", "spread"),
                default="start"
            ),
            "cross_policy": ChoiceField(
                ("stretch", "center", "end"),
                default="stretch"
            ),
            "same_extent": BoolField(default=False),
        },
        capabilities=("container", "layout"),
        layout=LayoutSpec(
            axis="horizontal",
            distribution_field="flow_policy",
            cross_alignment_field="cross_policy",
            equal_size_field="same_extent",
        ),
    )

    try:
        register_item_type(definition)
        item = create_item(
            kind,
            {
                "props": {
                    "gap": "7",
                    "flow_policy": "SPREAD",
                    "cross_policy": "center",
                    "same_extent": "false",
                },
                "items": [{"kind": "button"}],
            },
        )

        assert definition.is_layout
        assert definition.layout_axis == "horizontal"
        assert definition.layout_spec.distribution_field == "flow_policy"
        assert definition.layout_spec.cross_alignment_field == "cross_policy"
        assert definition.layout_spec.equal_size_field == "same_extent"
        assert item["props"] == {
            "gap": 7,
            "flow_policy": "spread",
            "cross_policy": "center",
            "same_extent": False,
        }
        assert item["items"][0]["kind"] == "button"
    finally:
        ITEM_TYPES.unregister(kind)


def test_synthetic_card_section_uses_field_owned_display_mode():
    kind = "card_section_test"
    ITEM_TYPES.unregister(kind)
    definition = ItemTypeDefinition(
        kind=kind,
        title="Card Section Test",
        category="Layout",
        fields={
            "display_mode": ChoiceField(
                ("cards", "stack"),
                default="cards"
            ),
        },
        capabilities=("container", "section"),
        section=SectionSpec(mode_field="display_mode"),
    )

    try:
        register_item_type(definition)
        document = normalize_document({
            "version": CONFIG_VERSION,
            "sections": [
                {
                    "kind": kind,
                    "id": "cards-id",
                    "name": "cards",
                    "ui": {},
                    "props": {"display_mode": "STACK"},
                    "bindings": [],
                    "items": [{"kind": "button"}],
                },
            ],
        })

        section = document["sections"][0]
        assert definition.is_section
        assert definition.section_spec.mode_field == "display_mode"
        assert not hasattr(definition.section_spec, "modes")
        assert definition.section_mode(section["props"]) == "stack"
        assert "folder_type" not in section["props"]
        assert section["items"][0]["kind"] == "button"

        with pytest.raises(FieldValidationError):
            definition.section_mode({"display_mode": "unsupported"})
    finally:
        ITEM_TYPES.unregister(kind)


def test_builtin_folder_row_column_metadata_is_definition_owned():
    folder = ITEM_TYPES.get("folder", required=True)
    row = ITEM_TYPES.get("row", required=True)
    column = ITEM_TYPES.get("column", required=True)

    assert folder.section_spec.mode_field == "folder_type"
    assert not hasattr(folder.section_spec, "modes")
    assert folder.section_mode({"folder_type": "tabs"}) == "tabs"
    assert row.layout_spec.axis == "horizontal"
    assert column.layout_spec.axis == "vertical"
