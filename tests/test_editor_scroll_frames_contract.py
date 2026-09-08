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


def test_editor_trees_use_external_frames_for_scroll_borders():
    source = _read(
        "scripts/script_toolbox/ui/editor_scroll_frames.py"
    )

    assert 'frame.setObjectName("EditorScrollFrame")' in source
    assert "border: 1px solid #161616;" in source
    assert "frame_layout.setContentsMargins(1, 1, 1, 1)" in source
    assert "widget.setFrameShape(QtGui.QFrame.NoFrame)" in source
    assert "border: 0px;" in source
    assert 'getattr(self, "palette", None)' in source
    assert 'getattr(self, "tree", None)' in source


def test_interface_editor_installs_scroll_frame_wrapper():
    source = _read(
        "scripts/script_toolbox/ui/__init__.py"
    )

    assert "build_scroll_frame_interface_editor_class" in source
    assert "InterfaceEditor = build_scroll_frame_interface_editor_class(" in source
