# -*- coding: utf-8 -*-
from __future__ import print_function

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path):
    return (
        ROOT / relative_path
    ).read_text(
        encoding="utf-8"
    )


def test_maya_uses_native_selection_changed_callback():
    source = _read(
        "scripts/script_toolbox/hosts/maya_host.py"
    )

    assert "EVENT_SELECTION_CHANGED" in source
    assert "cmds.scriptJob" in source
    assert '"SelectionChanged"' in source
    assert "kill=job_id" in source


def test_nuke_normalizes_update_ui_to_selection_changed():
    source = _read(
        "scripts/script_toolbox/hosts/nuke_host.py"
    )

    assert "EVENT_SELECTION_CHANGED" in source
    assert "nuke.addUpdateUI" in source
    assert "nuke.removeUpdateUI" in source
    assert "last_signature" in source


def test_runtime_prefers_callback_and_keeps_polling_fallback():
    source = _read(
        "scripts/script_toolbox/ui/debounced_main_window.py"
    )

    assert "HostCallbackGroup" in source
    assert "_install_host_callbacks" in source
    assert "self.selection_timer.stop()" in source
    assert "if not subscribed:" in source
    assert "self.clear_host_callbacks()" in source


def test_callback_layer_is_independent_from_links_and_editor():
    callbacks = _read(
        "scripts/script_toolbox/hosts/callbacks.py"
    )
    maya = _read(
        "scripts/script_toolbox/hosts/maya_host.py"
    )
    nuke = _read(
        "scripts/script_toolbox/hosts/nuke_host.py"
    )

    combined = callbacks + maya + nuke

    assert "core.references" not in combined
    assert "EditorDocumentController" not in combined
    assert "ItemsStateCommand" not in combined
