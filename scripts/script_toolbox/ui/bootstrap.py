# -*- coding: utf-8 -*-
from __future__ import print_function

from ..core.editor_document import EditorDocumentController
from ..core.logging_utils import get_logger
from . import debounced_main_window as _debounced_main_window_module
from . import interface_editor as _interface_editor_module
from . import runtime as _runtime_module
from . import runtime_renderers as _runtime_renderers_module
from .editor_document_adapter import build_interface_editor_class
from .editor_polish_hooks import install_icon_only_button_centering
from .editor_polish_hooks import install_runtime_icon_feedback
from .editor_selection_state import EditorSelectionStateMixin
from .item_ui_bootstrap import ensure_builtin_item_ui_bindings
from .preset_hooks import build_preset_interface_editor_class
from .reference_warning_hooks import build_reference_warning_editor_class
from .runtime_renderers import _decorate_runtime_renderer_registry
from .runtime_renderers import get_runtime_renderer_registry
from .runtime_renderers import initialize_runtime_renderer_registry
from .runtime_value_sync import synchronize_runtime_value_renderers
from .scroll_surface_frames import install_runtime_scroll_frames
from .telemetry_hooks import build_telemetry_interface_editor_class
from .telemetry_hooks import install_telemetry_share_controller
from .template_transfer_hooks import build_template_transfer_interface_editor_class


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


class _SelectableInterfaceEditor(EditorSelectionStateMixin,
                                 _interface_editor_module.InterfaceEditor):
    pass


def _compose_interface_editor():
    ensure_builtin_item_ui_bindings()
    base_editor = _SelectableInterfaceEditor

    editor_class = build_interface_editor_class(
        base_editor,
        controller_class=EditorDocumentController,
        layout_support=False,
        share_controller_factory=install_telemetry_share_controller
    )
    editor_class = build_reference_warning_editor_class(editor_class)
    editor_class = build_preset_interface_editor_class(editor_class)
    editor_class = build_template_transfer_interface_editor_class(editor_class)
    editor_class = build_telemetry_interface_editor_class(editor_class)


    return editor_class


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

    # Specialized startup wrappers are installed first. The shared generic
    # pipeline then becomes the outermost decoration for both initial and late
    # renderers, so event/value behavior is identical and marker-idempotent.
    install_runtime_scroll_frames(
        registry,
        _runtime_module
    )
    install_icon_only_button_centering(registry)
    install_runtime_icon_feedback(registry)
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
