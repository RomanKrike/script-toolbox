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


def test_standalone_hot_reload_suspends_auto_quit():
    source = _read(
        "scripts/script_toolbox/bootstrap.py"
    )

    assert "def _begin_standalone_window_transition" in source
    assert '"setQuitOnLastWindowClosed"' in source
    assert '"quitOnLastWindowClosed"' in source
    assert '"removePostedEvents"' in source
    assert '"Quit"' in source
    assert "transition = _begin_standalone_window_transition()" in source
    assert "_end_standalone_window_transition(" in source


def test_portable_smoke_covers_menu_editor_and_reload():
    source = _read(
        "tools/smoke_standalone_portable.py"
    )

    assert "window.open_interface_editor()" in source
    assert "menu.styleSheet() != STYLE" in source
    assert "hot_reload_toolbox()" in source
    assert "Standalone window did not reopen after hot reload." in source
