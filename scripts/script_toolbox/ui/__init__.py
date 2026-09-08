# -*- coding: utf-8 -*-

from .code_editor import CodeEditor
from .code_editor import ScriptHighlighter
from . import interface_editor as _interface_editor_module
from .editor_document_adapter import build_interface_editor_class
from .interface_tree import ExistingInterfaceTree


def _install_controls_v2_palette(editor_class):
    groups = []
    for group_label, entries in editor_class.PALETTE_GROUPS:
        entries = tuple(entries)
        if group_label == "ACTIONS" and not any(
            entry[1] == "icon"
            for entry in entries
        ):
            entries = entries + (
                (
                    "Icon",
                    "icon",
                    "Standalone image; optionally clickable through an On Click callback."
                ),
            )
        groups.append((group_label, entries))
    editor_class.PALETTE_GROUPS = tuple(groups)


_install_controls_v2_palette(
    _interface_editor_module.InterfaceEditor
)

InterfaceEditor = build_interface_editor_class(
    _interface_editor_module.InterfaceEditor
)

# Keep direct imports from script_toolbox.ui.interface_editor compatible while
# the legacy Qt dialog is gradually decomposed across STEP 07/08.
_interface_editor_module.InterfaceEditor = InterfaceEditor

# Install the runtime renderer registry before main_window imports
# build_folder_widgets from runtime. The legacy runtime module stays available
# as a compatibility implementation, while active kind dispatch is registry-
# based and can be extended without editing RuntimeFolder's if/elif chain.
from . import runtime as _runtime_module
from .runtime_renderers import get_runtime_renderer_registry
from .runtime_renderers import install_runtime_renderer_registry
from .runtime_renderers import register_runtime_renderer
from .runtime_renderers import unregister_runtime_renderer

install_runtime_renderer_registry(
    _runtime_module
)

from .main_window import ScriptToolbox
from .controls_v2_hooks import install_controls_v2_hooks
from .script_editor import ScriptEditorWidget
from .runtime import DisplayField
from .runtime import RuntimeFolder
from .runtime import RuntimeFolderRadio
from .runtime import RuntimeFolderTabs

install_controls_v2_hooks(
    _runtime_module,
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
