# -*- coding: utf-8 -*-

import os


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


def _bootstrap_namespace():
    path = os.path.join(
        ROOT,
        "scripts",
        "script_toolbox",
        "ui",
        "bootstrap.py"
    )
    with open(path, "r") as handle:
        source = handle.read()

    # Execute only declarations from UIComposition onward. Imports and the
    # real Qt/DCC dependency graph stay outside this unit-test boundary.
    source = source.split("class UIComposition(object):", 1)[1]
    source = "class UIComposition(object):" + source

    class _Logger(object):
        def __init__(self):
            self.exceptions = []

        def exception(self, message):
            self.exceptions.append(message)

    namespace = {
        "__name__": "ui_bootstrap_test",
        "_COMPOSITION_STATE": None,
        "_LOGGER": _Logger(),
        "_runtime_module": object(),
    }
    exec(
        compile(source, "ui/bootstrap.py", "exec"),
        namespace
    )
    return namespace


def test_initialize_ui_is_ordered_and_idempotent():
    namespace = _bootstrap_namespace()
    calls = []
    registry = object()

    def compose_editor():
        calls.append("editor")
        return "EditorClass"

    def compose_registry():
        calls.append("registry")
        return registry

    def compose_toolbox(active_registry):
        calls.append(("toolbox", active_registry))
        return "ToolboxClass"

    namespace["_compose_interface_editor"] = compose_editor
    namespace["_compose_runtime_registry"] = compose_registry
    namespace["_compose_toolbox"] = compose_toolbox

    first = namespace["initialize_ui"]()
    second = namespace["initialize_ui"]()

    assert first is second
    assert first.InterfaceEditor == "EditorClass"
    assert first.ScriptToolbox == "ToolboxClass"
    assert first.runtime_registry is registry
    assert calls == [
        "editor",
        "registry",
        ("toolbox", registry),
    ]


def test_initialize_ui_does_not_cache_failed_composition():
    namespace = _bootstrap_namespace()
    attempts = []

    def failing_editor():
        attempts.append("failed")
        raise RuntimeError("boom")

    namespace["_compose_interface_editor"] = failing_editor

    try:
        namespace["initialize_ui"]()
    except RuntimeError:
        pass
    else:
        raise AssertionError("Expected composition failure.")

    assert namespace["_COMPOSITION_STATE"] is None
    assert namespace["_LOGGER"].exceptions == [
        "UI composition bootstrap failed."
    ]

    namespace["_compose_interface_editor"] = lambda: "EditorClass"
    namespace["_compose_runtime_registry"] = lambda: "registry"
    namespace["_compose_toolbox"] = lambda registry: "ToolboxClass"

    state = namespace["initialize_ui"]()
    assert state.InterfaceEditor == "EditorClass"
    assert attempts == ["failed"]


def test_runtime_registry_reuses_same_runtime_module_on_bootstrap_reload():
    namespace = _bootstrap_namespace()
    runtime_module = object()
    active_registry = object()
    initialized = []

    class _RuntimeRenderersModule(object):
        _RUNTIME_MODULE = runtime_module

    namespace["_runtime_module"] = runtime_module
    namespace["_runtime_renderers_module"] = _RuntimeRenderersModule()
    namespace["get_runtime_renderer_registry"] = lambda: active_registry
    namespace["initialize_runtime_renderer_registry"] = (
        lambda runtime: initialized.append(runtime) or object()
    )

    assert namespace["_runtime_registry"]() is active_registry
    assert initialized == []


def test_runtime_registry_reinitializes_after_runtime_module_reload():
    namespace = _bootstrap_namespace()
    runtime_module = object()
    stale_registry = object()
    fresh_registry = object()
    initialized = []

    class _RuntimeRenderersModule(object):
        _RUNTIME_MODULE = object()

    namespace["_runtime_module"] = runtime_module
    namespace["_runtime_renderers_module"] = _RuntimeRenderersModule()
    namespace["get_runtime_renderer_registry"] = lambda: stale_registry

    def initialize(runtime):
        initialized.append(runtime)
        return fresh_registry

    namespace["initialize_runtime_renderer_registry"] = initialize

    assert namespace["_runtime_registry"]() is fresh_registry
    assert initialized == [runtime_module]
