# -*- coding: utf-8 -*-

import os


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


def _read(relative_path):
    path = os.path.join(ROOT, *relative_path.split("/"))
    with open(path, "r") as handle:
        return handle.read()


def test_ui_package_delegates_runtime_composition_to_explicit_bootstrap():
    package_source = _read("scripts/script_toolbox/ui/__init__.py")
    bootstrap_source = _read("scripts/script_toolbox/ui/bootstrap.py")

    assert "from .bootstrap import initialize_ui" in package_source
    assert "_RUNTIME = initialize_ui()" in package_source
    assert "initialize_runtime_renderer_registry(" not in package_source

    runtime_step = bootstrap_source.index(
        "runtime_registry = _compose_runtime_registry()"
    )
    toolbox_step = bootstrap_source.index(
        "toolbox_class = _compose_toolbox(runtime_registry)"
    )
    assert runtime_step < toolbox_step


def test_default_registry_is_built_from_item_type_renderer_metadata():
    source = _read("scripts/script_toolbox/ui/runtime_renderers.py")
    ui_bindings = _read("scripts/script_toolbox/ui/item_ui_bootstrap.py")

    assert "for definition in ITEM_TYPES.all():" in source
    assert "if definition.renderer is not None:" in source
    assert "definition.kind" in source
    assert "definition.renderer" in source

    expected = set([
        "folder",
        "row",
        "column",
        "button",
        "toggle_button",
        "icon",
        "toggle_icon",
        "checkbox",
        "field",
        "label",
        "text",
        "separator",
        "string",
        "integer",
        "float",
        "menu",
        "color",
        "image",
    ])

    for kind in expected:
        assert '("{0}",'.format(kind) in ui_bindings


def test_specialized_current_renderers_bind_through_item_type_metadata():
    source = _read("scripts/script_toolbox/ui/item_ui_bootstrap.py")

    assert '("row", render_row)' in source
    assert '("column", render_column)' in source
    assert '("text", render_text)' in source
    assert '("toggle_button", render_toggle_button)' in source
    assert '("toggle_icon", render_toggle_icon)' in source
    assert '("image", render_image)' in source
    assert "ITEM_TYPES.bind_ui(kind, renderer=renderer)" in source


def test_active_runtime_dispatch_is_registry_based_without_method_patch():
    runtime_source = _read("scripts/script_toolbox/ui/runtime.py")
    registry_source = _read("scripts/script_toolbox/ui/runtime_renderers.py")

    assert "def build_runtime_widget(" in runtime_source
    assert "get_runtime_renderer_registry" in runtime_source
    assert "return registry.render(" in runtime_source
    assert "_registry_build_runtime_widget" not in registry_source
    assert '"build_runtime_widget",' not in registry_source


def test_runtime_registry_stays_separate_from_link_remapping():
    core_source = _read("scripts/script_toolbox/core/runtime_registry.py")
    ui_source = _read("scripts/script_toolbox/ui/runtime_renderers.py")

    assert "references" not in core_source
    assert "references" not in ui_source
    assert "EditorDocumentController" not in core_source
    assert "EditorDocumentController" not in ui_source
