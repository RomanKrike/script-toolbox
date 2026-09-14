# -*- coding: utf-8 -*-
from __future__ import print_function

from ..fields import ChoiceField
from ..fields import IntField
from ..fields import PathField
from ..item_registry import ItemTypeDefinition


def image_definition():
    return ItemTypeDefinition(
        kind="image",
        title="Image",
        category="Display",
        description="Display a raster image with configurable fit mode.",
        order=50,
        fields={
            "source": PathField(default=""),
            "fit": ChoiceField(
                ("contain", "cover", "stretch"),
                default="contain"
            ),
            "width": IntField(default=200, minimum=8, maximum=4096),
            "height": IntField(default=120, minimum=8, maximum=4096),
        },
        events=("click", "double_click"),
        capabilities=("bindable", "resizable"),
        default_label="Image",
        ui_defaults={"show_label": False},
        renderer_path=".image_item:render_image",
        inspector_path=".image_item:ImagePropertyEditor",
    )


__all__ = [
    "image_definition",
]
