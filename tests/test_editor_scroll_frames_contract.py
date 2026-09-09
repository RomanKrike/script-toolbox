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


def test_editor_trees_use_shared_external_scroll_frames():
    source = _read(
        "scripts/script_toolbox/ui/editor_scroll_frames.py"
    )
    shared = _read(
        "scripts/script_toolbox/ui/scroll_surface_frames.py"
    )

    assert "from .scroll_surface_frames import wrap_scroll_widget" in source
    assert "def install_interface_editor_scroll_frames(editor):" in source
    assert 'getattr(editor, "palette", None)' in source
    assert 'getattr(editor, "tree", None)' in source
    assert "background=LIST_BG" in source
    assert "border=BORDER_PRESSED" in source
    assert "from ..style.palette import LIST_BG" in source
    assert "from ..style.palette import BORDER_PRESSED" in source

    assert 'frame.setObjectName("ScrollSurfaceFrame")' in shared
    assert "layout.setContentsMargins(1, 1, 1, 1)" in shared
    assert "widget.setFrameShape(QtGui.QFrame.NoFrame)" in shared
    assert "border: 0px;" in shared


def test_interface_editor_installs_scroll_frames_without_active_wrapper():
    ui_source = _read(
        "scripts/script_toolbox/ui/__init__.py"
    )
    search_source = _read(
        "scripts/script_toolbox/ui/editor_search.py"
    )

    assert "build_scroll_frame_interface_editor_class" not in ui_source
    assert "install_interface_editor_scroll_frames(self)" in search_source
    assert "from .editor_scroll_frames import install_interface_editor_scroll_frames" in search_source
