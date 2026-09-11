# -*- coding: utf-8 -*-

import os


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


def _read(relative_path):
    path = os.path.join(ROOT, *relative_path.split("/"))
    with open(path, "r") as handle:
        return handle.read()


def test_composition_root_routes_interface_editor_through_base_controller():
    source = _read("scripts/script_toolbox/ui/bootstrap.py")

    assert "from ..core.editor_document import EditorDocumentController" in source
    assert "from .editor_document_adapter import build_interface_editor_class" in source
    assert "editor_class = build_interface_editor_class(" in source
    assert "controller_class=EditorDocumentController" in source
    assert "layout_support=True" in source
    assert "LayoutEditorDocumentController" not in source


def test_adapter_owns_working_document_and_cache_through_controller():
    source = _read("scripts/script_toolbox/ui/editor_document_adapter.py")

    assert "EditorDocumentController" in source
    assert "controller_class=None" in source
    assert "self.document_controller = controller_class(" in source
    assert "def working(self):" in source
    assert "self.document_controller.adopt(document)" in source
    assert "def item_cache(self):" in source
    assert "self.document_controller.rebuild_index()" in source


def test_adapter_routes_structural_helpers_through_controller():
    source = _read("scripts/script_toolbox/ui/editor_document_adapter.py")

    assert "self.document_controller.used_names()" in source
    assert "self.document_controller.unique_name(" in source
    assert "self.document_controller.clone_subtree(" in source
    assert "self.document_controller.cache_subtree(data)" in source
    assert "self.document_controller.duplicate_name()" in source


def test_adapter_uses_command_history_not_document_snapshot_stacks():
    source = _read("scripts/script_toolbox/ui/editor_document_adapter.py")

    assert "CommandHistory(" in source
    assert "DocumentCapture(" in source
    assert "ItemStateCommand(" in source
    assert "build_document_delta(" in source
    assert "self.command_history.undo()" in source
    assert "self.command_history.redo()" in source


def test_layout_behavior_is_composed_inside_document_adapter():
    source = _read("scripts/script_toolbox/ui/editor_document_adapter.py")
    layout_source = _read("scripts/script_toolbox/ui/layout_editor_adapter.py")

    for helper in (
        "make_layout_tree_item",
        "fix_layout_tree_structure",
        "sync_layout_working_from_tree",
        "insert_layout_cloned_tree_item",
        "create_layout_from_palette",
        "delete_layout_selected",
    ):
        assert "from .layout_editor_adapter import {0}".format(helper) in source
        assert "def {0}(".format(helper) in layout_source

    assert "layout_support=False" in source
    assert "if not layout_support:" in source
    assert "apply_layout_property_context(" in source
    assert "build_layout_editor_class" not in layout_source
    assert "unwrap_layout_editor_base" not in layout_source


def test_apply_preserves_editor_view_state_without_forwarding_wrapper():
    source = _read("scripts/script_toolbox/ui/editor_document_adapter.py")
    ui_dir = os.path.join(ROOT, "scripts", "script_toolbox", "ui")

    assert "def capture_editor_view_state(editor):" in source
    assert "def restore_editor_view_state(editor, state):" in source
    assert "def _capture_tree_view_state(self):" in source
    assert "def _restore_tree_view_state(self, state):" in source
    assert not os.path.exists(os.path.join(ui_dir, "editor_view_state.py"))

    apply_source = source.split(
        "        def apply_changes(self):",
        1
    )[1].split("    setattr(", 1)[0]

    assert "view_state = self._capture_tree_view_state()" in apply_source
    assert "self.populate_tree()" in apply_source
    assert "self._restore_tree_view_state(" in apply_source


def test_adapter_reload_guard_is_current_adapter_only():
    source = _read("scripts/script_toolbox/ui/editor_document_adapter.py")

    assert '_ADAPTER_BASE = "_script_toolbox_interface_editor_adapter_base"' in source
    assert "_LEGACY_BASE" not in source
    assert "unwrap_layout_editor_base" not in source
    assert "Avoid stacking this active adapter" in source


def test_adapter_composes_search_and_share_directly():
    source = _read("scripts/script_toolbox/ui/editor_document_adapter.py")
    package_source = _read("scripts/script_toolbox/ui/__init__.py")
    bootstrap_source = _read("scripts/script_toolbox/ui/bootstrap.py")

    assert "from .editor_search import apply_editor_presentation" in source
    assert "from .editor_search import reapply_existing_filter" in source
    assert "from .share_hooks import install_share_controller" in source
    assert "install_share_controller(self)" in source
    assert "apply_editor_presentation(self)" in source
    assert "reapply_existing_filter(self)" in source

    for ui_source in (package_source, bootstrap_source):
        assert "build_search_interface_editor_class(" not in ui_source
        assert "build_share_interface_editor_class(" not in ui_source
