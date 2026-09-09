# -*- coding: utf-8 -*-

from .code_editor import CodeEditor
from .code_editor import ScriptHighlighter
from . import interface_editor as _interface_editor_module
from ..core.layout_document import LayoutEditorDocumentController
from .editor_document_adapter import build_interface_editor_class
from .editor_polish_hooks import install_icon_only_button_centering
from .editor_polish_hooks import install_icon_only_state_refresh
from .editor_polish_hooks import install_runtime_icon_feedback
from .interface_tree import ExistingInterfaceTree
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

        if group_label == "ACTIONS":
            updated = list(entries)

            if not any(
                entry[1] == "toggle_button"
                for entry in updated
            ):
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

            if not any(
                entry[1] == "icon"
                for entry in updated
            ):
                updated.append((
                    "Icon",
                    "icon",
                    "Standalone image with optional event bindings."
                ))

            entries = tuple(updated)

        groups.append((group_label, entries))
    editor_class.PALETTE_GROUPS = tuple(groups)


_install_controls_v2_palette(
    _interface_editor_module.InterfaceEditor
)

InterfaceEditor = build_interface_editor_class(
    _interface_editor_module.InterfaceEditor,
    controller_class=LayoutEditorDocumentController,
    layout_support=True
)
install_property_editor_scroll_frames()

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
from .toggle_button_runtime import install_toggle_button_event_hooks
from .toggle_button_runtime import install_toggle_button_main_window
from .toggle_button_runtime import render_toggle_button

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
register_runtime_renderer(
    "toggle_button",
    render_toggle_button
)
install_runtime_scroll_frames(
    get_runtime_renderer_registry(),
    _runtime_module
)

from .main_window import ScriptToolbox as _BaseScriptToolbox
from .update_channels_ui import build_update_channel_toolbox_class
from .controls_v2_hooks import install_controls_v2_hooks
from . import event_binding_hooks as _event_binding_hooks_module
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

# Runtime main-window hooks must be installed on the shared base class.
# bootstrap.py instantiates debounced_main_window.ScriptToolbox, which inherits
# from this base instead of the wrapper exported from script_toolbox.ui.
# Installing only on the wrapper leaves the live runtime without methods such
# as dispatch_binding_event.
install_controls_v2_hooks(
    _runtime_module,
    _BaseScriptToolbox
)

# Build the icon-only renderer before event bindings wrap the registry. This
# guarantees custom click/double-click bindings attach to the final button.
install_icon_only_button_centering(
    get_runtime_renderer_registry()
)
install_toggle_button_event_hooks(
    _event_binding_hooks_module
)
install_event_binding_hooks(
    get_runtime_renderer_registry(),
    _runtime_renderers_module,
    _BaseScriptToolbox
)
install_toggle_button_main_window(
    _BaseScriptToolbox
)
install_runtime_icon_feedback(
    get_runtime_renderer_registry()
)
install_icon_only_state_refresh(
    _BaseScriptToolbox
)

# Runtime value synchronization is installed after the renderer decorators so
# every active value renderer registers its final Qt control tree. Patch both
# the base store_value() implementation and the debounced runtime override;
# bootstrap.py uses the latter in Maya, Nuke and Houdini.
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
    "DisplayField",
    "RuntimeFolder",
    "RuntimeFolderRadio",
    "RuntimeFolderTabs",
    "get_runtime_renderer_registry",
    "register_runtime_renderer",
    "unregister_runtime_renderer",
]
