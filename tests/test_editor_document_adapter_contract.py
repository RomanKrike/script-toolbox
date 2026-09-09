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


def test_adapter_routes_structural_helpers_through_controller():
    source = _read(
        "scripts/script_toolbox/ui/editor_document_adapter.py"
    )

    assert "self.document_controller.used_names()" in source
    assert "self.document_controller.unique_name(" in source
    assert "self.document_controller.clone_subtree(" in source
    assert "self.document_controller.cache_subtree(data)" in source
    assert "self.document_controller.duplicate_name()" in source


def test_adapter_replaces_active_snapshot_history_with_commands():
    source = _read(
        "scripts/script_toolbox/ui/editor_document_adapter.py"
    )

    assert "CommandHistory(" in source
    assert "DocumentCapture(" in source
    assert "ItemStateCommand(" in source
    assert "build_document_delta(" in source
    assert "self.command_history.undo()" in source
    assert "self.command_history.redo()" in source
    assert "self.undo_stack = self.command_history.undo_stack" in source
    assert "self.redo_stack = self.command_history.redo_stack" in source


def test_property_history_coalescing_timer_is_preserved():
    source = _read(
        "scripts/script_toolbox/ui/editor_document_adapter.py"
    )
    legacy = _read(
        "scripts/script_toolbox/ui/interface_editor.py"
    )

    assert "self.history_timer.setInterval(300)" in legacy
    assert "def schedule_history(self):" in source
    assert "self.history_timer.start()" in source
    assert "def commit_history(self, sync_tree=True):" in source


def test_apply_bypasses_legacy_history_snapshot_bookkeeping():
    source = _read(
        "scripts/script_toolbox/ui/editor_document_adapter.py"
    )

    apply_source = source.split(
        "        def apply_changes(self):",
        1
    )[1]
    apply_source = apply_source.split(
        "    setattr(",
        1
    )[0]

    assert "base_class.apply_changes" not in apply_source
    assert "self.document_controller.snapshot()" in apply_source
    assert "self.document_controller.replace(" in apply_source
    assert "_history_current" not in apply_source


def test_adapter_composes_presentation_and_share_without_extra_wrapper():
    source = _read(
        "scripts/script_toolbox/ui/editor_document_adapter.py"
    )
    ui_source = _read(
        "scripts/script_toolbox/ui/__init__.py"
    )

    assert "from .editor_search import apply_editor_presentation" in source
    assert "from .editor_search import filter_existing_parameters as filter_editor_structure" in source
    assert "from .editor_search import reapply_existing_filter" in source
    assert "from .share_hooks import install_share_controller" in source
    assert "install_share_controller(self)" in source
    assert "def build_ui(self):" in source
    assert "apply_editor_presentation(self)" in source
    assert "def filter_existing_parameters(self, value):" in source
    assert "filter_editor_structure(" in source
    assert "def populate_tree(self):" in source
    assert "reapply_existing_filter(self)" in source

    assert "build_search_interface_editor_class(" not in ui_source
    assert "from .editor_search" not in ui_source
    assert "build_share_interface_editor_class(" not in ui_source


def test_apply_preserves_view_state_inside_document_adapter():
    source = _read(
        "scripts/script_toolbox/ui/editor_document_adapter.py"
    )
    ui_source = _read(
        "scripts/script_toolbox/ui/__init__.py"
    )

    assert "def capture_editor_view_state(editor):" in source
    assert "def restore_editor_view_state(editor, state):" in source
    assert "def _capture_tree_view_state(self):" in source
    assert "def _restore_tree_view_state(self, state):" in source

    apply_source = source.split(
        "        def apply_changes(self):",
        1
    )[1].split(
        "    setattr(",
        1
    )[0]

    assert "view_state = self._capture_tree_view_state()" in apply_source
    assert "self.populate_tree()" in apply_source
    assert "self._restore_tree_view_state(" in apply_source
    assert apply_source.index(
        "view_state = self._capture_tree_view_state()"
    ) < apply_source.index(
        "self.toolbox.rebuild()"
    )
    assert apply_source.index(
        "self.populate_tree()"
    ) < apply_source.index(
        "self._restore_tree_view_state("
    )

    assert "build_editor_view_state_class" not in ui_source
    assert "from .editor_view_state" not in ui_source


def test_legacy_view_state_builder_delegates_to_adapter_helpers():
    source = _read(
        "scripts/script_toolbox/ui/editor_view_state.py"
    )

    assert "from .editor_document_adapter import capture_editor_view_state" in source
    assert "from .editor_document_adapter import restore_editor_view_state" in source
    assert "def build_editor_view_state_class(base_class):" in source
    assert "capture_editor_view_state(" in source
    assert "restore_editor_view_state(" in source
