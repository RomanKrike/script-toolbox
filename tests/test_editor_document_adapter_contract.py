# -*- coding: utf-8 -*-

import os


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


def _read(relative_path):
    path = os.path.join(
        ROOT,
        *relative_path.split("/")
    )
    with open(path, "r") as handle:
        return handle.read()


def test_ui_package_routes_interface_editor_through_controller_adapter():
    source = _read(
        "scripts/script_toolbox/ui/__init__.py"
    )

    assert "from .editor_document_adapter import build_interface_editor_class" in source
    assert "InterfaceEditor = build_interface_editor_class(" in source
    assert "_interface_editor_module.InterfaceEditor = InterfaceEditor" in source


def test_adapter_owns_working_document_and_cache_through_controller():
    source = _read(
        "scripts/script_toolbox/ui/editor_document_adapter.py"
    )

    assert "EditorDocumentController" in source
    assert "def working(self):" in source
    assert "self.document_controller.adopt(document)" in source
    assert "def item_cache(self):" in source
    assert "self.document_controller.rebuild_index()" in source


def test_adapter_factory_unwraps_previous_adapter_on_reload():
    source = _read(
        "scripts/script_toolbox/ui/editor_document_adapter.py"
    )

    assert "def _unwrap_base(base_class):" in source
    assert "while getattr(base_class, _ADAPTER_MARKER, False):" in source
    assert "def build_interface_editor_class(base_class):" in source
    assert "_LEGACY_BASE" in source


def test_adapter_routes_structural_helpers_without_replacing_history_yet():
    source = _read(
        "scripts/script_toolbox/ui/editor_document_adapter.py"
    )
    legacy = _read(
        "scripts/script_toolbox/ui/interface_editor.py"
    )

    assert "self.document_controller.used_names()" in source
    assert "self.document_controller.unique_name(" in source
    assert "self.document_controller.clone_subtree(" in source
    assert "self.document_controller.cache_subtree(data)" in source
    assert "self.document_controller.duplicate_name()" in source

    # STEP 08 owns the history rewrite. STEP 07 must retain the existing
    # snapshot stacks so this PR cannot silently mix both roadmap steps.
    assert "self.undo_stack = []" in legacy
    assert "copy.deepcopy(self._history_current)" in legacy
