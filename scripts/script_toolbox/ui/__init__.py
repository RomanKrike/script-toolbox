# -*- coding: utf-8 -*-

from .code_editor import CodeEditor
from .code_editor import ScriptHighlighter
from . import interface_editor as _interface_editor_module
from . import editor_document_adapter as _editor_document_adapter_module
from ..core.layout_document import LayoutEditorDocumentController
from .editor_document_adapter import build_interface_editor_class
from .editor_polish_hooks import install_editor_search_ux
from .editor_polish_hooks import install_icon_only_button_centering
from .editor_polish_hooks import install_icon_only_state_refresh
from .editor_polish_hooks import install_runtime_icon_feedback
from .editor_view_state import build_editor_view_state_class
from .icon_ui_hooks import build_icon_interface_editor_class
from .icon_ui_hooks import install_property_icon_browse
from .icon_ui_hooks import install_script_editor_icons
from .layout_editor_adapter import build_layout_editor_class
from .layout_context import install_layout_property_context
from .share_hooks import build_share_interface_editor_class
from .editor_scroll_frames import build_scroll_frame_interface_editor_class
from .interface_tree import ExistingInterfaceTree
from .property_pane_style import install_property_pane_style
from .properties.base import PropertyEditorBase
from .properties.button import ButtonPropertyEditor
from .properties.icon import IconPropertyEditor
from .scroll_surface_frames import install_property_editor_scroll_frames
from .scroll_surface_frames import install_runtime_scroll_frames
from .scroll_surface_frames import install_script_editor_scroll_frames


def _install_controls_v2_palette(editor_class):
    groups = []
    for group_label, entries in editor_class.PALETTE_GROUPS:
        entries = tuple(entries)

        if group_label == "LAYOUT" and not any(
            entry[1] == "column"
            for entry in entries
        ):
            updated = []
            for entry in entries:
                updated.append(entry)
                if entry[1] == "row":
                    updated.append((
                        "Column",
                        "column",
                        "Vertical layout for stacking controls, Rows and Columns."
                    ))
            entries = tuple(updated)

        if group_label == "ACTIONS" and not any(
            entry[1] == "icon"
            for entry in entries
        ):
            entries = entries + (
                (
                    "Icon",
                    "icon",
                    "Standalone image with optional event bindings."
                ),
            )
        groups.append((group_label, entries))
    editor_class.PALETTE_GROUPS = tuple(groups)


_install_controls_v2_palette(
    _interface_editor_module.InterfaceEditor
)

_layout_editor_class = build_layout_editor_class(
    _interface_editor_module.InterfaceEditor
)
install_layout_property_context(
    _layout_editor_class
)

# The command/history adapter resolves this module global when constructing its
# controller. Use the layout-aware controller without changing the legacy core
# controller contract for older direct imports.
_editor_document_adapter_module.EditorDocumentController = (
    LayoutEditorDocumentController
)

InterfaceEditor = build_interface_editor_class(
    _layout_editor_class
)
InterfaceEditor = build_editor_view_state_class(
    InterfaceEditor
)
InterfaceEditor = build_share_interface_editor_class(
    InterfaceEditor
)
InterfaceEditor = build_icon_interface_editor_class(
    InterfaceEditor
)
InterfaceEditor = build_scroll_frame_interface_editor_class(
    InterfaceEditor
)
install_property_pane_style(
    InterfaceEditor,
    PropertyEditorBase
)
install_property_icon_browse(
    ButtonPropertyEditor,
    IconPropertyEditor
)
install_property_editor_scroll_frames()
install_editor_search_ux(
    InterfaceEditor
)

# Keep direct imports from script_toolbox.ui.interface_editor compatible while
# the legacy Qt dialog is gradually decomposed across STEP 07/08.
_interface_editor_module.InterfaceEditor = InterfaceEditor

# Install the runtime renderer registry before main_window imports
# build_folder_widgets from runtime. The legacy runtime module stays available
# as a compatibility implementation, while active kind dispatch is registry-
# based and can be extended without editing RuntimeFolder's if/elif chain.
from . import runtime as _runtime_module
from . import runtime_renderers as _runtime_renderers_module
from .column_layout import render_column
from .row_layout import render_row
from .runtime_renderers import get_runtime_renderer_registry
from .runtime_renderers import install_runtime_renderer_registry
from .runtime_renderers import register_runtime_renderer
from .runtime_renderers import unregister_runtime_renderer

install_runtime_renderer_registry(
    _runtime_module
)
register_runtime_renderer(
    "row",
    render_row,
    replace=True
)
register_runtime_renderer(
    "column",
    render_column
)
install_runtime_scroll_frames(
    get_runtime_renderer_registry(),
    _runtime_module
)

from .main_window import ScriptToolbox as _BaseScriptToolbox
from .update_channels_ui import build_update_channel_toolbox_class
from .controls_v2_hooks import install_controls_v2_hooks
from .event_binding_hooks import install_event_binding_hooks
from .script_editor import ScriptEditorWidget
from .runtime import DisplayField
from .runtime import RuntimeFolder
from .runtime import RuntimeFolderRadio
from .runtime import RuntimeFolderTabs

ScriptToolbox = build_update_channel_toolbox_class(
    _BaseScriptToolbox
)

install_script_editor_scroll_frames(
    ScriptEditorWidget
)
install_script_editor_icons(
    ScriptEditorWidget
)

install_controls_v2_hooks(
    _runtime_module,
    ScriptToolbox
)

install_event_binding_hooks(
    get_runtime_renderer_registry(),
    _runtime_renderers_module,
    ScriptToolbox
)
install_runtime_icon_feedback(
    get_runtime_renderer_registry()
)
install_icon_only_button_centering(
    get_runtime_renderer_registry()
)
install_icon_only_state_refresh(
    ScriptToolbox
)

__all__ = [
    "CodeEditor",
    "ScriptHighlighter",
    "InterfaceEditor",
    "ExistingInterfaceTree",
    "ScriptToolbox",
    "ScriptEditorWidget",
    "DisplayField",
    "RuntimeFolder",
    "RuntimeFolderRadio",
    "RuntimeFolderTabs",
    "get_runtime_renderer_registry",
    "register_runtime_renderer",
    "unregister_runtime_renderer",
]
