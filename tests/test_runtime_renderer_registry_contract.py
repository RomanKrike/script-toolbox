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
    definitions = _read("scripts/script_toolbox/model/item_builtins.py")
    ui_bootstrap = _read("scripts/script_toolbox/ui/item_ui_bootstrap.py")

    assert "for definition in ITEM_TYPES.all():" in source
    assert "if definition.renderer is not None:" in source
    assert "definition.kind" in source
    assert "definition.renderer" in source
    assert "for definition in ITEM_TYPES.all():" in ui_bootstrap
    assert "definition.renderer_path" in ui_bootstrap

    expected_paths = (
        ".runtime_renderers:_render_folder",
        ".row_layout:render_row",
        ".column_layout:render_column",
        ".runtime_renderers:_render_button",
        ".toggle_button_runtime:render_toggle_button",
        ".runtime_renderers:_render_icon",
        ".toggle_icon_runtime:render_toggle_icon",
        ".runtime_renderers:_render_checkbox",
        ".runtime_renderers:_render_field",
        ".runtime_renderers:_render_label",
        ".text_runtime:render_text",
        ".runtime_renderers:_render_separator",
        ".runtime_renderers:_render_string",
        ".runtime_renderers:_render_integer",
        ".runtime_renderers:_render_float",
        ".runtime_renderers:_render_menu",
        ".runtime_renderers:_render_color",
        ".image_item:render_image",
    )

    for path in expected_paths:
        assert 'renderer_path="{0}"'.format(path) in definitions


def test_specialized_current_renderers_are_definition_owned():
    definitions = _read("scripts/script_toolbox/model/item_builtins.py")
    ui_bootstrap = _read("scripts/script_toolbox/ui/item_ui_bootstrap.py")

    assert 'renderer_path=".row_layout:render_row"' in definitions
    assert 'renderer_path=".column_layout:render_column"' in definitions
    assert 'renderer_path=".text_runtime:render_text"' in definitions
    assert (
        'renderer_path=".toggle_button_runtime:render_toggle_button"'
        in definitions
    )
    assert (
        'renderer_path=".toggle_icon_runtime:render_toggle_icon"'
        in definitions
    )
    assert 'renderer_path=".image_item:render_image"' in definitions
    assert "ITEM_TYPES.bind_ui(" in ui_bootstrap
    assert '"row"' not in ui_bootstrap
    assert '"column"' not in ui_bootstrap
    assert '"image"' not in ui_bootstrap


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
