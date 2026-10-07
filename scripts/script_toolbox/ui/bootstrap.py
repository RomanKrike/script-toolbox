# -*- coding: utf-8 -*-
from __future__ import print_function

from ..core.logging_utils import get_logger
from . import debounced_main_window as _debounced_main_window_module
from . import runtime as _runtime_module
from . import runtime_renderers as _runtime_renderers_module
from .composed_editor import InterfaceEditor
from .item_ui_bootstrap import ensure_builtin_item_ui_bindings
from .runtime_renderers import _decorate_runtime_renderer_registry
from .runtime_renderers import get_runtime_renderer_registry
from .runtime_renderers import initialize_runtime_renderer_registry
from .runtime_value_sync import synchronize_runtime_value_renderers


_LOGGER = get_logger()
_COMPOSITION_STATE = None


class UIComposition(object):
    """Final UI/runtime objects produced by the package composition root."""

    def __init__(
        self,
        interface_editor_class,
        toolbox_class,
        runtime_registry
    ):
        self.InterfaceEditor = interface_editor_class
        self.ScriptToolbox = toolbox_class
        self.runtime_registry = runtime_registry
        self.runtime_module = _runtime_module


def _compose_interface_editor():
    ensure_builtin_item_ui_bindings()
    return InterfaceEditor


def _runtime_registry():
    registry = get_runtime_renderer_registry()
    current_runtime = getattr(
        _runtime_renderers_module,
        "_RUNTIME_MODULE",
        None
    )

    if registry is None or current_runtime is not _runtime_module:
        registry = initialize_runtime_renderer_registry(_runtime_module)

    return registry


def _compose_runtime_registry():
    ensure_builtin_item_ui_bindings()
    registry = _runtime_registry()

    # Each raw renderer receives the same presentation/events/value pipeline.
    _decorate_runtime_renderer_registry(registry)
    return registry


def _compose_toolbox(runtime_registry):
    toolbox_class = _debounced_main_window_module.ScriptToolbox

    synchronize_runtime_value_renderers(runtime_registry)
    return toolbox_class


def initialize_ui():
    """Build the final UI/runtime composition exactly once per module graph."""
    global _COMPOSITION_STATE

    if _COMPOSITION_STATE is not None:
        return _COMPOSITION_STATE

    try:
        ensure_builtin_item_ui_bindings()
        interface_editor_class = _compose_interface_editor()
        runtime_registry = _compose_runtime_registry()
        toolbox_class = _compose_toolbox(runtime_registry)
        state = UIComposition(
            interface_editor_class,
            toolbox_class,
            runtime_registry
        )
    except Exception:
        _LOGGER.exception("UI composition bootstrap failed.")
        raise

    _COMPOSITION_STATE = state
    return state


__all__ = [
    "UIComposition",
    "initialize_ui",
]
