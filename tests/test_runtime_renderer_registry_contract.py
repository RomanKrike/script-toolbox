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


def test_default_registry_covers_native_base_runtime_kinds():
    source = _read("scripts/script_toolbox/ui/runtime_renderers.py")

    expected = set([
        "folder",
        "row",
        "button",
        "icon",
        "checkbox",
        "field",
        "label",
        "separator",
        "string",
        "integer",
        "float",
        "menu",
        "color",
    ])

    for kind in expected:
        assert '("{0}", _render_'.format(kind) in source

    assert '("toggle", _render_' not in source


def test_specialized_current_kinds_are_owned_by_composition_root():
    source = _read("scripts/script_toolbox/ui/bootstrap.py")

    assert 'registry.register("row", render_row, replace=True)' in source
    assert 'registry.register("column", render_column, replace=True)' in source
    assert 'registry.register("text", render_text, replace=True)' in source
    assert (
        'registry.register("toggle_button", render_toggle_button, replace=True)'
        in source
    )
    assert (
        'registry.register("toggle_icon", render_toggle_icon, replace=True)'
        in source
    )


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
