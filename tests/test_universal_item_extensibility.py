# -*- coding: utf-8 -*-

import importlib.util
import os
import sys
import types

from script_toolbox.core.runtime_registry import RuntimeRendererRegistry
from script_toolbox.model.bindings import binding_events
from script_toolbox.model.fields import BoolField
from script_toolbox.model.fields import ChoiceField
from script_toolbox.model.fields import PathField
from script_toolbox.model.item_registry import ITEM_TYPES
from script_toolbox.model.item_registry import ItemTypeDefinition
from script_toolbox.model.item_registry import register_item_type
from script_toolbox.model.items import create_item


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)
UI_ROOT = os.path.join(
    ROOT,
    "scripts",
    "script_toolbox",
    "ui"
)


def _source(*parts):
    path = os.path.join(ROOT, *parts)
    with open(path, "r") as handle:
        return handle.read()


def _load_module(monkeypatch, name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, module)
    spec.loader.exec_module(module)
    return module


def _install_synthetic_ui_package(monkeypatch):
    import script_toolbox

    package = types.ModuleType("script_toolbox.ui")
    package.__package__ = "script_toolbox.ui"
    package.__path__ = [UI_ROOT]
    monkeypatch.setitem(sys.modules, "script_toolbox.ui", package)
    monkeypatch.setattr(script_toolbox, "ui", package, raising=False)

    compat = types.ModuleType("script_toolbox.compat")
    compat.QtCore = types.SimpleNamespace()
    compat.QtGui = types.SimpleNamespace()
    monkeypatch.setitem(sys.modules, "script_toolbox.compat", compat)

    style = types.ModuleType("script_toolbox.style")
    style.__path__ = []
    monkeypatch.setitem(sys.modules, "script_toolbox.style", style)

    metrics = types.ModuleType("script_toolbox.style.metrics")
    metrics.RUNTIME_PARAMETER_SPACING = 4
    monkeypatch.setitem(sys.modules, "script_toolbox.style.metrics", metrics)

    palette = types.ModuleType("script_toolbox.style.palette")
    palette.TEXT_SUBTLE = "#888888"
    monkeypatch.setitem(sys.modules, "script_toolbox.style.palette", palette)

    event_hooks = types.ModuleType("script_toolbox.ui.event_binding_hooks")
    event_hooks.calls = []

    def install_event_binding_hooks(registry):
        event_hooks.calls.append(registry)
        return True

    event_hooks.install_event_binding_hooks = install_event_binding_hooks
    monkeypatch.setitem(
        sys.modules,
        "script_toolbox.ui.event_binding_hooks",
        event_hooks
    )

    value_sync = types.ModuleType("script_toolbox.ui.runtime_value_sync")
    value_sync.calls = []

    def synchronize_runtime_value_renderers(registry):
        value_sync.calls.append(registry)
        return registry

    value_sync.synchronize_runtime_value_renderers = (
        synchronize_runtime_value_renderers
    )
    monkeypatch.setitem(
        sys.modules,
        "script_toolbox.ui.runtime_value_sync",
        value_sync
    )

    ui_bootstrap = _load_module(
        monkeypatch,
        "script_toolbox.ui.item_ui_bootstrap",
        os.path.join(UI_ROOT, "item_ui_bootstrap.py")
    )
    item_palette = _load_module(
        monkeypatch,
        "script_toolbox.ui.item_palette",
        os.path.join(UI_ROOT, "item_palette.py")
    )
    runtime_renderers = _load_module(
        monkeypatch,
        "script_toolbox.ui.runtime_renderers",
        os.path.join(UI_ROOT, "runtime_renderers.py")
    )
    return ui_bootstrap, item_palette, runtime_renderers, event_hooks, value_sync


class VideoInspector(object):
    pass


def render_video(owner, item, compact=False):
    return (
        item["props"]["source"],
        item["props"]["fit"],
        bool(compact),
    )


def test_video_registers_after_ui_bootstrap_without_core_changes(monkeypatch):
    kind = "video"
    ITEM_TYPES.unregister(kind)

    original_bindings = [
        (definition, definition.renderer, definition.inspector)
        for definition in ITEM_TYPES.all()
    ]

    def existing_renderer(owner, item, compact=False):
        return None

    class ExistingInspector(object):
        pass

    try:
        # Simulate an already-composed UI without importing the real Qt stack.
        for definition, renderer, inspector in original_bindings:
            ITEM_TYPES.bind_ui(
                definition.kind,
                renderer=(
                    renderer
                    if renderer is not None
                    else existing_renderer
                ),
                inspector=(
                    inspector
                    if inspector is not None
                    else ExistingInspector
                )
            )

        (
            ui_bootstrap,
            item_palette,
            runtime_renderers,
            event_hooks,
            value_sync,
        ) = _install_synthetic_ui_package(monkeypatch)

        active_registry = RuntimeRendererRegistry()
        for definition in ITEM_TYPES.all():
            active_registry.register(
                definition.kind,
                definition.renderer
            )
        runtime_renderers._ACTIVE_REGISTRY = active_registry

        plugin_module = types.ModuleType(
            "script_toolbox.ui.video_test_plugin"
        )
        plugin_module.render_video = render_video
        plugin_module.VideoInspector = VideoInspector
        monkeypatch.setitem(
            sys.modules,
            "script_toolbox.ui.video_test_plugin",
            plugin_module
        )

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
            renderer_path=".video_test_plugin:render_video",
            inspector_path=".video_test_plugin:VideoInspector",
        )
        register_item_type(definition)

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
        assert definition in ITEM_TYPES.creatable()
        assert binding_events(kind) == ("click", "double_click")

        # Re-entrant UI bootstrap resolves a definition registered after the
        # original UI composition.
        ui_bootstrap.ensure_builtin_item_ui_bindings()
        assert definition.renderer is render_video
        assert definition.inspector is VideoInspector

        # The already-active runtime registry discovers the late definition
        # without any central kind -> renderer edit.
        registry = runtime_renderers.get_runtime_renderer_registry()
        assert registry is active_registry
        assert registry.has(kind)
        assert registry.render(None, item, compact=True) == (
            "preview.mp4",
            "cover",
            True,
        )
        assert event_hooks.calls[-1] is registry
        assert value_sync.calls[-1] is registry

        palette_kinds = [
            entry[1]
            for group_label, entries in item_palette.palette_groups()
            for entry in entries
        ]
        assert kind in palette_kinds
    finally:
        if "runtime_renderers" in locals():
            registry = runtime_renderers._ACTIVE_REGISTRY
            if registry is not None:
                registry.unregister(kind)
        ITEM_TYPES.unregister(kind)
        for definition, renderer, inspector in original_bindings:
            ITEM_TYPES.bind_ui(
                definition.kind,
                renderer=renderer,
                inspector=inspector
            )


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

    palette_source = _source(
        "scripts", "script_toolbox", "ui", "item_palette.py"
    )
    assert "ITEM_TYPES.creatable()" in palette_source


def test_central_routing_symbols_are_not_required_by_item_architecture():
    import script_toolbox.model.items as items_module
    import script_toolbox.model.bindings as bindings_module
    import script_toolbox.model.layouts as layouts_module

    assert not hasattr(items_module, "_FACTORIES")
    assert not hasattr(bindings_module, "EVENT_CAPABILITIES")
    assert not hasattr(layouts_module, "LAYOUT_KINDS")
    assert not hasattr(layouts_module, "CONTAINER_KINDS")
