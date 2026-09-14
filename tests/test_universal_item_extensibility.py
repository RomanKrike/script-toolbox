# -*- coding: utf-8 -*-

import os

from script_toolbox.core.runtime_registry import RuntimeRendererRegistry
from script_toolbox.model.bindings import binding_events
from script_toolbox.model.fields import BoolField
from script_toolbox.model.fields import ChoiceField
from script_toolbox.model.fields import PathField
from script_toolbox.model.item_registry import ITEM_TYPES
from script_toolbox.model.item_registry import ItemTypeDefinition
from script_toolbox.model.items import create_item
from script_toolbox.ui.item_palette import palette_groups


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


def _source(*parts):
    path = os.path.join(ROOT, *parts)
    with open(path, "r") as handle:
        return handle.read()


class VideoInspector(object):
    pass


def render_video(owner, item, compact=False):
    return (
        item["props"]["source"],
        item["props"]["fit"],
        bool(compact),
    )


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
            "loop": BoolField(default=False),
            "fit": ChoiceField(
                ("contain", "cover", "stretch"),
                default="contain"
            ),
        },
        events=("click", "double_click"),
        capabilities=("bindable", "resizable"),
        default_label="Video",
        renderer=render_video,
        inspector=VideoInspector,
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
                    "loop": True,
                    "fit": "cover",
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
            "loop": True,
            "fit": "cover",
        }
        assert item["ui"]["label"] == "Video"
        assert ITEM_TYPES.get(kind) is definition
        assert definition in ITEM_TYPES.creatable()
        assert definition.inspector is VideoInspector
        assert binding_events(kind) == ("click", "double_click")

        groups = dict(palette_groups())
        assert any(
            entry[1] == kind
            for entry in groups["DISPLAY"]
        )

        registry = RuntimeRendererRegistry()
        registry.register(kind, definition.renderer)
        assert registry.render(None, item, compact=True) == (
            "preview.mp4",
            "cover",
            True,
        )
    finally:
        ITEM_TYPES.unregister(kind)


def test_video_extension_does_not_exist_in_core_routing_modules():
    for parts in (
        ("scripts", "script_toolbox", "model", "items.py"),
        ("scripts", "script_toolbox", "model", "bindings.py"),
        ("scripts", "script_toolbox", "model", "layouts.py"),
        ("scripts", "script_toolbox", "ui", "runtime_renderers.py"),
        ("scripts", "script_toolbox", "ui", "properties", "registry.py"),
        ("scripts", "script_toolbox", "ui", "interface_editor.py"),
        ("scripts", "script_toolbox", "ui", "item_palette.py"),
    ):
        assert '"video"' not in _source(*parts).lower()


def test_central_routing_symbols_are_not_required_by_item_architecture():
    import script_toolbox.model.items as items_module
    import script_toolbox.model.bindings as bindings_module
    import script_toolbox.model.layouts as layouts_module

    assert not hasattr(items_module, "_FACTORIES")
    assert not hasattr(bindings_module, "EVENT_CAPABILITIES")
    assert not hasattr(layouts_module, "LAYOUT_KINDS")
    assert not hasattr(layouts_module, "CONTAINER_KINDS")
