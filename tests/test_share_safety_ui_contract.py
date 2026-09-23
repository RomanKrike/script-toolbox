# -*- coding: utf-8 -*-

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHARE_HOOKS = (
    ROOT /
    "scripts" /
    "script_toolbox" /
    "ui" /
    "share_hooks.py"
)


def _method_source(source, name, next_marker):
    start = source.index("    def {0}(".format(name))
    end = source.index(next_marker, start)
    return source[start:end]


def test_shared_toolbox_gate_runs_before_import_mutation():
    source = SHARE_HOOKS.read_text(encoding="utf-8")
    function = _method_source(
        source,
        "_shared_settings_ready",
        "    def share_selected("
    )

    gate = function.index("self._allow_shared_import(")
    normalize = function.index("normalize_document(")
    sync = function.index("editor.sync_working_from_tree()")
    capture = function.index("DocumentCapture(")

    assert gate < normalize < sync < capture


def test_shared_item_gate_runs_before_item_creation_and_tree_mutation():
    source = SHARE_HOOKS.read_text(encoding="utf-8")
    function = _method_source(
        source,
        "_shared_item_ready",
        "\ndef install_share_controller("
    )

    gate = function.index("self._allow_shared_import(")
    create = function.index("create_item(")
    sync = function.index("editor.sync_working_from_tree()")
    insert = function.index("editor._insert_cloned_tree_item(")

    assert gate < create < sync < insert


def test_executable_warning_defaults_to_cancel():
    source = SHARE_HOOKS.read_text(encoding="utf-8")
    function = _method_source(
        source,
        "_show_executable_import_warning",
        "    def _allow_shared_import("
    )

    assert '"Cancel"' in function
    assert '"Import Anyway"' in function
    assert "setDefaultButton(\n            cancel_button" in function
    assert "setEscapeButton(\n            cancel_button" in function
