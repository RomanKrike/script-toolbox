# -*- coding: utf-8 -*-

from .code_editor import CodeEditor
from .code_editor import ScriptHighlighter
from . import interface_editor as _interface_editor_module
from . import editor_document_adapter as _editor_document_adapter_module
from ..core.editor_document import EditorDocumentController
from ..core.runtime_registry import install_registry_hook_once
from .editor_document_adapter import build_interface_editor_class
from .editor_polish_hooks import install_icon_only_button_centering
from .editor_polish_hooks import install_runtime_icon_feedback
from .editor_selection_state import install_editor_selection_state
from .interface_tree import ExistingInterfaceTree
from .preset_hooks import build_preset_interface_editor_class
from .reference_warning_hooks import build_reference_warning_editor_class
from .scroll_surface_frames import install_property_editor_scroll_frames
from .scroll_surface_frames import install_runtime_scroll_frames
from .scroll_surface_frames import install_script_editor_scroll_frames
from .telemetry_hooks import build_telemetry_interface_editor_class
from .telemetry_hooks import install_telemetry_share_controller
from .state_toggle_hooks import install_state_toggle_behavior


def _install_current_palette(editor_class):
    groups = []
    for group_label, entries in editor_class.PALETTE_GROUPS:
        entries = tuple(entries)

        if group_label == "LAYOUT":
            updated = list(entries)

            if not any(
                entry[1] == "column"
                for entry in updated
            ):
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

            if not any(
                entry[1] == "text"
                for entry in updated
            ):
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


_install_current_palette(_interface_editor_module.InterfaceEditor)
install_editor_selection_state(_interface_editor_module.InterfaceEditor)

# The controller adapter resolves this module global when an editor instance is
# constructed. Replacing it here ensures share-button signals are wired to the
# telemetry-aware controller from the start rather than swapping controllers
# after Qt signal connections already exist.
_editor_document_adapter_module.install_share_controller = (
    install_telemetry_share_controller
)

InterfaceEditor = build_interface_editor_class(
    _interface_editor_module.InterfaceEditor,
    controller_class=EditorDocumentController,
    layout_support=True
)
InterfaceEditor = build_reference_warning_editor_class(
    InterfaceEditor
)
InterfaceEditor = build_preset_interface_editor_class(
    InterfaceEditor
)
InterfaceEditor = build_telemetry_interface_editor_class(
    InterfaceEditor
)
install_property_editor_scroll_frames()
_interface_editor_module.InterfaceEditor = InterfaceEditor

from . import runtime as _runtime_module
from .collapsible_folder import CollapsibleSection
from .collapsible_folder import install_runtime_folder_composition

install_runtime_folder_composition(_runtime_module)

from .runtime_renderers import get_runtime_renderer_registry
from .runtime_renderers import initialize_runtime_renderer_registry
from .runtime_renderers import register_runtime_renderer
from .runtime_renderers import unregister_runtime_renderer
from .column_layout import render_column
from .row_layout import render_row
from .text_runtime import render_text
from .toggle_button_runtime import render_toggle_button
from .toggle_icon_runtime import render_toggle_icon

initialize_runtime_renderer_registry(_runtime_module)
register_runtime_renderer("row", render_row, replace=True)
register_runtime_renderer("column", render_column)
register_runtime_renderer("text", render_text)
register_runtime_renderer("toggle_button", render_toggle_button)
register_runtime_renderer("toggle_icon", render_toggle_icon)
install_runtime_scroll_frames(
    get_runtime_renderer_registry(),
    _runtime_module
)

from .main_window import ScriptToolbox as _BaseScriptToolbox

install_state_toggle_behavior(_BaseScriptToolbox)

from .update_channels_ui import build_update_channel_toolbox_class
from .event_binding_hooks import install_event_binding_hooks
from .script_editor import ScriptEditorWidget
from .runtime import DisplayField
from .runtime import RuntimeFolder
from .runtime import RuntimeFolderRadio
from .runtime import RuntimeFolderTabs

ScriptToolbox = build_update_channel_toolbox_class(_BaseScriptToolbox)

install_script_editor_scroll_frames(ScriptEditorWidget)
install_icon_only_button_centering(get_runtime_renderer_registry())
install_registry_hook_once(
    get_runtime_renderer_registry(),
    "_script_toolbox_event_bindings_installed",
    install_event_binding_hooks
)
install_runtime_icon_feedback(get_runtime_renderer_registry())

from .runtime_value_sync import install_runtime_value_sync
from . import debounced_main_window as _debounced_main_window_module

install_runtime_value_sync(
    get_runtime_renderer_registry(),
    _BaseScriptToolbox,
    store_toolbox_classes=(
        _debounced_main_window_module._DebouncedScriptToolbox,
    )
)

__all__ = [
    "CodeEditor",
    "ScriptHighlighter",
    "InterfaceEditor",
    "ExistingInterfaceTree",
    "ScriptToolbox",
    "ScriptEditorWidget",
    "CollapsibleSection",
    "DisplayField",
    "RuntimeFolder",
    "RuntimeFolderRadio",
    "RuntimeFolderTabs",
    "get_runtime_renderer_registry",
    "register_runtime_renderer",
    "unregister_runtime_renderer",
]
