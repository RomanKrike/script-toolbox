# -*- coding: utf-8 -*-
from __future__ import print_function

from ..core.editor_document import EditorDocumentController
from ..core.logging_utils import get_logger
from . import editor_document_adapter as _editor_document_adapter_module
from . import interface_editor as _interface_editor_module
from . import runtime as _runtime_module
from . import runtime_renderers as _runtime_renderers_module
from . import debounced_main_window as _debounced_main_window_module
from .collapsible_folder import install_runtime_folder_composition
from .column_layout import render_column
from .editor_document_adapter import build_interface_editor_class
from .editor_polish_hooks import install_icon_only_button_centering
from .editor_polish_hooks import install_runtime_icon_feedback
from .editor_selection_state import install_editor_selection_state
from .event_binding_hooks import install_event_binding_hooks
from .main_window import ScriptToolbox as _BaseScriptToolbox
from .preset_hooks import build_preset_interface_editor_class
from .reference_warning_hooks import build_reference_warning_editor_class
from .row_layout import render_row
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
from .text_runtime import render_text
from .toggle_button_runtime import render_toggle_button
from .toggle_icon_runtime import render_toggle_icon
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


def _install_current_palette(editor_class):
    """Install currently supported item kinds on the base editor palette."""
    groups = []
    for group_label, entries in editor_class.PALETTE_GROUPS:
        entries = tuple(entries)

        if group_label == "LAYOUT":
            updated = list(entries)

            if not any(entry[1] == "column" for entry in updated):
                insert_at = len(updated)
                for index, entry in enumerate(updated):
                    if entry[1] == "row":
                        insert_at = index + 1
                        break
                updated.insert(
                    insert_at,
                    (
                        "Column",
                        "column",
                        "Vertical layout for stacking controls, Rows and Columns."
                    )
                )

            if not any(entry[1] == "text" for entry in updated):
                insert_at = len(updated)
                for index, entry in enumerate(updated):
                    if entry[1] == "label":
                        insert_at = index + 1
                        break
                updated.insert(
                    insert_at,
                    (
                        "Text",
                        "text",
                        "Multiline static explanatory text with automatic word wrapping."
                    )
                )

            entries = tuple(updated)

        if group_label == "ACTIONS":
            updated = list(entries)

            if not any(entry[1] == "toggle_button" for entry in updated):
                insert_at = len(updated)
                for index, entry in enumerate(updated):
                    if entry[1] == "button":
                        insert_at = index + 1
                        break
                updated.insert(
                    insert_at,
                    (
                        "Toggle Button",
                        "toggle_button",
                        "Stateful ON/OFF action with internal or scripted state."
                    )
                )

            if not any(entry[1] == "icon" for entry in updated):
                updated.append((
                    "Icon",
                    "icon",
                    "Standalone image with optional event bindings."
                ))

            if not any(entry[1] == "toggle_icon" for entry in updated):
                insert_at = len(updated)
                for index, entry in enumerate(updated):
                    if entry[1] == "icon":
                        insert_at = index + 1
                        break
                updated.insert(
                    insert_at,
                    (
                        "Toggle Icon",
                        "toggle_icon",
                        "Stateful ON/OFF icon with independent images and actions."
                    )
                )

            entries = tuple(updated)

        groups.append((group_label, entries))

    editor_class.PALETTE_GROUPS = tuple(groups)


def _compose_interface_editor():
    base_editor = _interface_editor_module.InterfaceEditor
    _install_current_palette(base_editor)
    install_editor_selection_state(base_editor)

    # Transitional compatibility: the controller adapter still resolves its
    # share installer through a module global. Keeping this assignment inside
    # the explicit composition root makes the remaining monkeypatch visible
    # and contained until the adapter dependency can be made explicit without
    # breaking direct third-party builder imports.
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

    # Preserve the historical direct module import while the public package
    # export points at the same final composed class.
    _interface_editor_module.InterfaceEditor = editor_class
    return editor_class


def _runtime_registry():
    registry = get_runtime_renderer_registry()
    current_runtime = getattr(
        _runtime_renderers_module,
        "_RUNTIME_MODULE",
        None
    )

    # Reuse the active registry when only bootstrap is reloaded. This keeps
    # third-party runtime registrations and all idempotency markers intact.
    # A genuinely reloaded runtime module gets a fresh default registry.
    if registry is None or current_runtime is not _runtime_module:
        registry = initialize_runtime_renderer_registry(_runtime_module)

    return registry


def _compose_runtime_registry():
    install_runtime_folder_composition(_runtime_module)
    registry = _runtime_registry()

    # Built-ins owned by composition are explicit replacements. Re-running
    # bootstrap therefore cannot create duplicate registrations.
    registry.register("row", render_row, replace=True)
    registry.register("column", render_column, replace=True)
    registry.register("text", render_text, replace=True)
    registry.register("toggle_button", render_toggle_button, replace=True)
    registry.register("toggle_icon", render_toggle_icon, replace=True)

    install_runtime_scroll_frames(
        registry,
        _runtime_module
    )
    install_icon_only_button_centering(registry)
    install_event_binding_hooks(registry)
    install_runtime_icon_feedback(registry)
    return registry


def _compose_toolbox(runtime_registry):
    install_state_toggle_behavior(_BaseScriptToolbox)
    toolbox_class = build_update_channel_toolbox_class(
        _BaseScriptToolbox
    )

    install_script_editor_scroll_frames(ScriptEditorWidget)
    install_runtime_value_sync(
        runtime_registry,
        _BaseScriptToolbox,
        store_toolbox_classes=(
            _debounced_main_window_module._DebouncedScriptToolbox,
        )
    )
    return toolbox_class


def initialize_ui():
    """Build the final UI/runtime composition exactly once per module graph.

    The function is intentionally idempotent. The package keeps calling it at
    import time for public-import compatibility, but all ordering and mutation
    now live in this single composition root rather than in ``ui.__init__``.
    """
    global _COMPOSITION_STATE

    if _COMPOSITION_STATE is not None:
        return _COMPOSITION_STATE

    try:
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
