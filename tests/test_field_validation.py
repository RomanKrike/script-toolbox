# -*- coding: utf-8 -*-

from script_toolbox.model.fields import BoolField
from script_toolbox.model.fields import ChoiceField
from script_toolbox.model.fields import ColorField
from script_toolbox.model.fields import FloatField
from script_toolbox.model.fields import IntField
from script_toolbox.model.fields import ListField
from script_toolbox.model.fields import PathField
from script_toolbox.model.fields import TextField
from script_toolbox.model.item_registry import ItemTypeDefinition


def test_scalar_fields_expose_validation_separately_from_normalization():
    integer = IntField(default=2, minimum=0, maximum=4)
    floating = FloatField(default=0.5, minimum=0.0, maximum=1.0)
    choice = ChoiceField(("contain", "cover", "stretch"), default="contain")
    boolean = BoolField(default=False)

    assert integer.validate(3)
    assert not integer.validate(9)
    assert not integer.validate("bad")
    assert integer.normalize(9) == 4

    assert floating.validate(0.25)
    assert not floating.validate(2.0)
    assert floating.normalize(2.0) == 1.0

    assert choice.validate("COVER")
    assert not choice.validate("crop")
    assert choice.normalize("crop") == "contain"

    assert boolean.validate(True)
    assert not boolean.validate(1)
    assert boolean.normalize(1) is True


def test_color_list_path_and_custom_validation_contracts():
    color = ColorField()
    items = ListField(
        default=[],
        item_field=IntField(minimum=0, maximum=10),
        minimum=1,
        maximum=3,
    )
    path = PathField(default="")
    text = TextField(default="", validator=lambda value: len(value) <= 4)

    assert color.validate([0.0, 0.5, 1.0])
    assert not color.validate([0.0, 2.0, 1.0])
    assert not color.validate([0.0, 1.0])

    assert items.validate([1, 2, 3])
    assert not items.validate([])
    assert not items.validate([1, 20])
    assert not items.validate([1, 2, 3, 4])

    assert path.validate("D:/refs/front.png")
    assert text.validate("abcd")
    assert not text.validate("abcde")


def test_item_definition_reports_declarative_field_validation_errors():
    definition = ItemTypeDefinition(
        kind="sample",
        title="Sample",
        fields={
            "count": IntField(default=1, minimum=1, maximum=4),
            "mode": ChoiceField(("a", "b"), default="a"),
        },
    )

    assert definition.validate_props({
        "count": 2,
        "mode": "b",
    }) == {}

    errors = definition.validate_props({
        "count": 10,
        "mode": "c",
    })
    assert set(errors) == set(("count", "mode"))
