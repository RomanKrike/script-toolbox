# -*- coding: utf-8 -*-
from __future__ import print_function

from ..core.editor_document import EditorDocumentController
from ..core.logging_utils import get_logger
from . import debounced_main_window as _debounced_main_window_module
from . import editor_document_adapter as _editor_document_adapter_module
from . import interface_editor as _interface_editor_module
from . import runtime as _runtime_module
from . import runtime_renderers as _runtime_renderers_module
from .collapsible_folder import install_runtime_folder_composition
from .editor_document_adapter import build_interface_editor_class
from .editor_polish_hooks import install_icon_only_button_centering
from .editor_polish_hooks import install_runtime_icon_feedback
from .editor_selection_state import install_editor_selection_state
from .event_binding_hooks import install_event_binding_hooks
from .item_palette import install_registry_palette
from .item_runtime_adapter import build_item_aware_toolbox_class
from .item_ui_bootstrap import ensure_builtin_item_ui_bindings
from .main_window import ScriptToolbox as _BaseScriptToolbox
from .preset_hooks import build_preset_interface_editor_class
from .reference_warning_hooks import build_reference_warning_editor_class
from .runtime_renderers import get_runtime_renderer_registry
from .runtime_renderers import initialize_runtime_renderer_registry
from .runtime_value_sync import install_runtime_value_sync
from .script_editor import ScriptEditorWidget
from .scroll_surface_frames import install_property_editor_scroll_frames
from .scroll_surface_frames import install_runtime_scroll_frames
from .scroll_surface_frames import install_script_editor_scroll_frames
from .state_toggle_hooks import install_state_toggle_behavior
from .telemetry_hooks import build_telemetry_interface_editor_class
from .telemetry_hooks import install_telemetry_share_controller
from .update_channels_ui import build_update_channel_toolbox_class


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
    base_editor = _interface_editor_module.InterfaceEditor
    install_registry_palette(base_editor)
    install_editor_selection_state(base_editor)

    # The controller adapter still resolves its share installer through a
    # module global. Keep that mutation in the explicit composition root.
    _editor_document_adapter_module.install_share_controller = (
        install_telemetry_share_controller
    )

    editor_class = build_interface_editor_class(
        base_editor,
        controller_class=EditorDocumentController,
        layout_support=True
    )
    editor_class = build_reference_warning_editor_class(editor_class)
    editor_class = build_preset_interface_editor_class(editor_class)
    editor_class = build_telemetry_interface_editor_class(editor_class)

    install_property_editor_scroll_frames()

    _interface_editor_module.InterfaceEditor = editor_class
    return editor_class


def _runtime_registry():
    registry = get_runtime_renderer_registry()
    current_runtime = getattr(
        _runtime_renderers_module,
        "_RUNTIME_MODULE",
        None
    )

    # Reuse the active registry when only bootstrap is reloaded. A genuinely
    # reloaded runtime module gets a fresh registry rebuilt from ItemType data.
    if registry is None or current_runtime is not _runtime_module:
        registry = initialize_runtime_renderer_registry(_runtime_module)

    return registry


def _compose_runtime_registry():
    ensure_builtin_item_ui_bindings()
    install_runtime_folder_composition(_runtime_module)
    registry = _runtime_registry()

    install_runtime_scroll_frames(
        registry,
        _runtime_module
    )
    install_icon_only_button_centering(registry)
    install_event_binding_hooks(registry)
    install_runtime_icon_feedback(registry)
    return registry


def _compose_toolbox(runtime_registry):
    item_aware_base = build_item_aware_toolbox_class(_BaseScriptToolbox)
    install_state_toggle_behavior(item_aware_base)
    toolbox_class = build_update_channel_toolbox_class(
        item_aware_base
    )

    install_script_editor_scroll_frames(ScriptEditorWidget)
    install_runtime_value_sync(
        runtime_registry,
        item_aware_base,
        store_toolbox_classes=(
            _debounced_main_window_module._DebouncedScriptToolbox,
        )
    )
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
