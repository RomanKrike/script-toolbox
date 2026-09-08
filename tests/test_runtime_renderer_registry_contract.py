# -*- coding: utf-8 -*-

import os


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


def _read(relative_path):
    path = os.path.join(
        ROOT,
        *relative_path.split("/")
    )
    with open(path, "r") as handle:
        return handle.read()


def test_ui_installs_registry_before_main_window_import():
    source = _read(
        "scripts/script_toolbox/ui/__init__.py"
    )

    install = source.index(
        "install_runtime_renderer_registry("
    )
    main_window = source.index(
        "from .main_window import ScriptToolbox"
    )

    assert install < main_window
    assert "register_runtime_renderer" in source
    assert "unregister_runtime_renderer" in source


def test_default_registry_covers_every_existing_runtime_kind():
    source = _read(
        "scripts/script_toolbox/ui/runtime_renderers.py"
    )

    expected = set([
        "folder",
        "row",
        "button",
        "toggle",
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


def test_active_runtime_dispatch_is_registry_based():
    source = _read(
        "scripts/script_toolbox/ui/runtime_renderers.py"
    )

    assert "def _registry_build_runtime_widget(" in source
    assert "return registry.render(" in source
    assert '"build_runtime_widget",' in source
    assert "_registry_build_runtime_widget" in source


def test_runtime_registry_stays_separate_from_link_remapping():
    core_source = _read(
        "scripts/script_toolbox/core/runtime_registry.py"
    )
    ui_source = _read(
        "scripts/script_toolbox/ui/runtime_renderers.py"
    )

    assert "references" not in core_source
    assert "references" not in ui_source
    assert "EditorDocumentController" not in core_source
    assert "EditorDocumentController" not in ui_source
