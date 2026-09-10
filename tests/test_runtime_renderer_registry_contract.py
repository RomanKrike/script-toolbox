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


def test_ui_initializes_registry_before_main_window_import():
    source = _read("scripts/script_toolbox/ui/__init__.py")

    initialize = source.index("initialize_runtime_renderer_registry(")
    main_window = source.index("from .main_window import ScriptToolbox")

    assert initialize < main_window
    assert "register_runtime_renderer" in source
    assert "unregister_runtime_renderer" in source


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


def test_specialized_current_kinds_register_through_public_registry():
    source = _read("scripts/script_toolbox/ui/__init__.py")

    assert 'register_runtime_renderer("column", render_column)' in source
    assert 'register_runtime_renderer("toggle_button", render_toggle_button)' in source
    assert 'register_runtime_renderer("toggle_icon", render_toggle_icon)' in source


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
