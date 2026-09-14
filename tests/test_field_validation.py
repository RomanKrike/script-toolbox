# -*- coding: utf-8 -*-

import pytest

from script_toolbox.model.fields import BoolField
from script_toolbox.model.fields import ChoiceField
from script_toolbox.model.fields import ColorField
from script_toolbox.model.fields import FieldValidationError
from script_toolbox.model.fields import FloatField
from script_toolbox.model.fields import IntField
from script_toolbox.model.fields import ListField
from script_toolbox.model.fields import PathField
from script_toolbox.model.fields import TextField
from script_toolbox.model.item_registry import ItemTypeDefinition
from script_toolbox.model.item_registry import ItemValidationError


def test_scalar_field_coercion_and_bounds_contract():
    integer = IntField(default=2, minimum=0, maximum=4)
    floating = FloatField(default=0.5, minimum=0.0, maximum=1.0)
    choice = ChoiceField(("contain", "cover", "stretch"), default="contain")

    assert integer.normalize("3") == 3
    assert integer.normalize(9) == 4
    assert integer.validate(4)
    assert not integer.validate(9)
    with pytest.raises(FieldValidationError):
        integer.normalize("bad")
    with pytest.raises(FieldValidationError):
        integer.normalize(1.5)

    assert floating.normalize("0.25") == 0.25
    assert floating.normalize(2.0) == 1.0
    assert floating.validate(1.0)
    with pytest.raises(FieldValidationError):
        floating.normalize("bad")

    assert choice.normalize("COVER") == "cover"
    assert choice.validate("cover")
    with pytest.raises(FieldValidationError):
        choice.normalize("crop")


def test_bool_field_never_uses_python_truthiness_for_arbitrary_strings():
    boolean = BoolField(default=False)

    assert boolean.normalize(True) is True
    assert boolean.normalize(False) is False
    assert boolean.normalize(1) is True
    assert boolean.normalize(0) is False
    assert boolean.normalize("true") is True
    assert boolean.normalize("TRUE") is True
    assert boolean.normalize("yes") is True
    assert boolean.normalize("false") is False
    assert boolean.normalize("FALSE") is False
    assert boolean.normalize("no") is False
    assert boolean.normalize("0") is False

    for value in ("hello", "off-ish", 2, -1, [], {}):
        with pytest.raises(FieldValidationError):
            boolean.normalize(value)


def test_color_list_path_text_and_custom_validation_contracts():
    color = ColorField()
    items = ListField(
        default=[],
        item_field=IntField(minimum=0, maximum=10),
        minimum=1,
        maximum=3,
    )
    path = PathField(default="")
    text = TextField(default="", validator=lambda value: len(value) <= 4)

    assert color.normalize([0, "0.5", 2]) == [0.0, 0.5, 1.0]
    assert color.validate([0.0, 0.5, 1.0])
    with pytest.raises(FieldValidationError):
        color.normalize([0.0, "bad", 1.0])
    with pytest.raises(FieldValidationError):
        color.normalize([0.0, 1.0])

    assert items.normalize([1, "2", 20, 5]) == [1, 2, 10]
    assert items.normalize(3) == [3]
    assert items.normalize([]) == [0]
    assert items.validate([1, 2, 3])
    with pytest.raises(FieldValidationError):
        items.normalize([1, "bad"])

    assert path.normalize("D:/refs/front.png") == "D:/refs/front.png"
    assert text.normalize("abcd") == "abcd"
    with pytest.raises(FieldValidationError):
        text.normalize("abcde")


def test_item_definition_validation_accepts_coercible_and_rejects_invalid():
    definition = ItemTypeDefinition(
        kind="sample",
        title="Sample",
        fields={
            "count": IntField(default=1, minimum=1, maximum=4),
            "mode": ChoiceField(("a", "b"), default="a"),
        },
    )

    assert definition.validate_props({
        "count": "2",
        "mode": "B",
    }) == {}

    errors = definition.validate_props({
        "count": "bad",
        "mode": "c",
    })
    assert set(errors) == set(("count", "mode"))

    normalized = definition.normalize_props({
        "count": "9",
        "mode": "B",
    })
    assert normalized == {"count": 4, "mode": "b"}

    with pytest.raises(ItemValidationError) as caught:
        definition.normalize_props(
            {"count": "bad", "mode": "a"},
            item_id="sample-id",
            item_name="sample_name"
        )
    error = caught.value
    assert error.kind == "sample"
    assert error.field == "count"
    assert error.item_id == "sample-id"
    assert error.item_name == "sample_name"
    assert error.value == "bad"
