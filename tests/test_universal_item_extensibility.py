# -*- coding: utf-8 -*-

from script_toolbox.model.fields import BoolField
from script_toolbox.model.fields import PathField
from script_toolbox.model.item_registry import ITEM_TYPES
from script_toolbox.model.item_registry import ItemTypeDefinition
from script_toolbox.model.items import create_item


def test_custom_video_item_registers_without_core_kind_tables():
    kind = "video"
    ITEM_TYPES.unregister(kind)
    definition = ItemTypeDefinition(
        kind=kind,
        title="Video",
        category="Display",
        fields={
            "source": PathField(default=""),
            "autoplay": BoolField(default=False),
        },
        events=("click", "double_click"),
        capabilities=("bindable", "resizable"),
        default_label="Video",
        renderer_path=".video_item:render_video",
        inspector_path=".video_item:VideoPropertyEditor",
    )

    ITEM_TYPES.register(definition)
    try:
        item = create_item(
            kind,
            {
                "name": "preview_video",
                "props": {
                    "source": "preview.mp4",
                    "autoplay": True,
                },
            },
        )

        assert item["kind"] == kind
        assert item["name"] == "preview_video"
        assert set(item) == set((
            "kind",
            "id",
            "name",
            "ui",
            "props",
            "bindings",
        ))
        assert item["props"] == {
            "source": "preview.mp4",
            "autoplay": True,
        }
        assert item["ui"]["label"] == "Video"
        assert ITEM_TYPES.get(kind) is definition
        assert definition in ITEM_TYPES.creatable()
        assert definition.renderer_path == ".video_item:render_video"
        assert definition.inspector_path == ".video_item:VideoPropertyEditor"
    finally:
        ITEM_TYPES.unregister(kind)


def test_central_routing_symbols_are_not_required_by_item_architecture():
    import script_toolbox.model.items as items_module
    import script_toolbox.model.bindings as bindings_module
    import script_toolbox.model.layouts as layouts_module

    assert not hasattr(items_module, "_FACTORIES")
    assert not hasattr(bindings_module, "EVENT_CAPABILITIES")
    assert not hasattr(layouts_module, "LAYOUT_KINDS")
    assert not hasattr(layouts_module, "CONTAINER_KINDS")
