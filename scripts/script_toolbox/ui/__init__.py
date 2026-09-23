# -*- coding: utf-8 -*-

from .bootstrap import initialize_ui


# Public imports historically compose the complete runtime automatically.
# Keep that compatibility contract, but make the side effect one explicit,
# idempotent call into the package composition root.
_RUNTIME = initialize_ui()

InterfaceEditor = _RUNTIME.InterfaceEditor
ScriptToolbox = _RUNTIME.ScriptToolbox

from .code_editor import CodeEditor
from .code_editor import ScriptHighlighter
from .collapsible_folder import CollapsibleSection
from .interface_tree import ExistingInterfaceTree
from .runtime import DisplayField
from .runtime import RuntimeFolder
from .runtime import RuntimeFolderRadio
from .runtime import RuntimeFolderTabs
from .runtime_renderers import get_runtime_renderer_registry
from .runtime_renderers import register_runtime_renderer
from .runtime_renderers import unregister_runtime_renderer
from .script_editor import ScriptEditorWidget


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
    "initialize_ui",
    "register_runtime_renderer",
    "unregister_runtime_renderer",
]
