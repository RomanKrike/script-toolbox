# -*- coding: utf-8 -*-

from .code_editor import CodeEditor
from .code_editor import ScriptHighlighter
from . import interface_editor as _interface_editor_module
from .editor_document_adapter import build_interface_editor_class
from .interface_tree import ExistingInterfaceTree

InterfaceEditor = build_interface_editor_class(
    _interface_editor_module.InterfaceEditor
)

# Keep direct imports from script_toolbox.ui.interface_editor compatible while
# the legacy Qt dialog is gradually decomposed across STEP 07/08.
_interface_editor_module.InterfaceEditor = InterfaceEditor

from .main_window import ScriptToolbox
from .script_editor import ScriptEditorWidget
from .runtime import DisplayField
from .runtime import RuntimeFolder
from .runtime import RuntimeFolderRadio
from .runtime import RuntimeFolderTabs

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
]
