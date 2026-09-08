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


def test_debounced_runtime_installs_update_channel_wrapper():
    source = _read(
        "scripts/script_toolbox/ui/debounced_main_window.py"
    )

    assert (
        "from .update_channels_ui import "
        "build_update_channel_toolbox_class"
    ) in source
    assert "_DebouncedScriptToolbox = ScriptToolbox" in source
    assert (
        "ScriptToolbox = build_update_channel_toolbox_class(\n"
        "    _DebouncedScriptToolbox\n"
        ")"
    ) in source


def test_bootstrap_still_launches_debounced_runtime_window():
    source = _read(
        "scripts/script_toolbox/bootstrap.py"
    )

    assert (
        "from .ui.debounced_main_window import show as _show"
    ) in source
