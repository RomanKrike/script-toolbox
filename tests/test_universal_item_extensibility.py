# -*- coding: utf-8 -*-

import importlib.util
import os
import sys
import types

from script_toolbox.constants import CONFIG_VERSION
from script_toolbox.core.runtime_registry import RuntimeRendererRegistry
from script_toolbox.core.values import get_value
from script_toolbox.core.values import store_value
from script_toolbox.model.bindings import binding_events
from script_toolbox.model.fields import BoolField
from script_toolbox.model.fields import ChoiceField
from script_toolbox.model.fields import PathField
from script_toolbox.model.fields import TextField
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
    event_hooks.marker = "_test_event_decorated"

    def install_event_binding_hooks(registry):
        event_hooks.calls.append(registry)
        for kind in registry.kinds():
            if not binding_events(kind):
                continue
            renderer = registry.renderer_for(kind)
            if getattr(renderer, event_hooks.marker, False):
                continue

            def event_wrapper(owner, item, compact=False, original=renderer):
                return original(owner, item, compact=compact)

            event_wrapper.__dict__.update(
                getattr(renderer, "__dict__", {})
            )
            setattr(event_wrapper, event_hooks.marker, True)
            registry.register(kind, event_wrapper, replace=True)
        return True

    event_hooks.install_event_binding_hooks = install_event_binding_hooks
    monkeypatch.setitem(
        sys.modules,
        "script_toolbox.ui.event_binding_hooks",
        event_hooks
    )

    value_sync = types.ModuleType("script_toolbox.ui.runtime_value_sync")
    value_sync.calls = []
    value_sync.marker = "_test_value_decorated"

    def synchronize_runtime_value_renderers(registry):
        value_sync.calls.append(registry)
        for definition in ITEM_TYPES.all():
            if not definition.has_capability("has_value"):
                continue
            renderer = registry.renderer_for(definition.kind)
            if renderer is None or getattr(renderer, value_sync.marker, False):
                continue

            def value_wrapper(owner, item, compact=False, original=renderer):
                return original(owner, item, compact=compact)

            value_wrapper.__dict__.update(
                getattr(renderer, "__dict__", {})
            )
            setattr(value_wrapper, value_sync.marker, True)
            registry.register(definition.kind, value_wrapper, replace=True)
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
        item["props"]["value"],
        bool(compact),
    )


def test_video_registers_after_ui_bootstrap_with_full_generic_pipeline(monkeypatch):
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
                "value": TextField(default=""),
            },
            events=("click", "double_click", "value_changed"),
            capabilities=("bindable", "resizable", "has_value"),
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
                    "autoplay": "true",
                    "loop": "false",
                    "fit": "COVER",
                    "value": "frame-1",
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
            "loop": False,
            "fit": "cover",
            "value": "frame-1",
        }
        assert item["ui"]["label"] == "Video"
        assert definition in ITEM_TYPES.creatable()
        assert binding_events(kind) == (
            "click",
            "double_click",
            "value_changed",
        )

        # Re-entrant UI bootstrap resolves a definition registered after the
        # original UI composition.
        ui_bootstrap.ensure_builtin_item_ui_bindings()
        assert definition.renderer is render_video
        assert definition.inspector is VideoInspector

        # The already-active runtime registry discovers the late definition
        # and applies the complete shared generic decoration pipeline.
        registry = runtime_renderers.get_runtime_renderer_registry()
        assert registry is active_registry
        assert registry.has(kind)
        decorated = registry.renderer_for(kind)
        assert getattr(decorated, event_hooks.marker, False)
        assert getattr(decorated, value_sync.marker, False)
        assert registry.render(None, item, compact=True) == (
            "preview.mp4",
            "cover",
            "frame-1",
            True,
        )
        assert event_hooks.calls[-1] is registry
        assert value_sync.calls[-1] is registry

        # Repeated decoration is semantically idempotent: no wrapper stacking.
        before = registry.renderer_for(kind)
        runtime_renderers._decorate_runtime_renderer_registry(registry)
        after = registry.renderer_for(kind)
        assert after is before

        # An initially-populated registry receives the same generic markers.
        initial_registry = RuntimeRendererRegistry()
        initial_registry.register(kind, render_video)
        runtime_renderers._decorate_runtime_renderer_registry(initial_registry)
        initial = initial_registry.renderer_for(kind)
        assert getattr(initial, event_hooks.marker, False)
        assert getattr(initial, value_sync.marker, False)

        palette_kinds = [
            entry[1]
            for group_label, entries in item_palette.palette_groups()
            for entry in entries
        ]
        assert kind in palette_kinds

        # has_value participates in the same model schema for runtime writes.
        document = {
            "version": CONFIG_VERSION,
            "sections": [
                create_item(
                    "folder",
                    {
                        "name": "video_section",
                        "items": [item],
                    },
                )
            ],
        }
        assert get_value(document, "preview_video") == "frame-1"
        store_value(document, "preview_video", "frame-2")
        assert get_value(document, "preview_video") == "frame-2"

        # Explicit runtime unregister must not be undone by generic sync.
        assert runtime_renderers.unregister_runtime_renderer(kind) is render_video
        assert not registry.has(kind)
        assert runtime_renderers.get_runtime_renderer_registry() is registry
        assert not registry.has(kind)

        # A subsequent explicit registration re-enables and decorates renderer.
        runtime_renderers.register_runtime_renderer(kind, render_video)
        renderer = registry.renderer_for(kind)
        assert getattr(renderer, event_hooks.marker, False)
        assert getattr(renderer, value_sync.marker, False)
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
