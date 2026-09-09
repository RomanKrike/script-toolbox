# -*- coding: utf-8 -*-
from __future__ import print_function

from ..style.palette import BORDER_PRESSED
from ..style.palette import LIST_BG
from .scroll_surface_frames import wrap_scroll_widget


def install_interface_editor_scroll_frames(editor):
    """Apply shared scroll-surface frames directly to one editor instance."""
    if getattr(editor, "_interface_scroll_frames_installed", False):
        return
    editor._interface_scroll_frames_installed = True

    editor.palette_scroll_frame = wrap_scroll_widget(
        getattr(editor, "palette", None),
        background=LIST_BG,
        border=BORDER_PRESSED
    )
    editor.tree_scroll_frame = wrap_scroll_widget(
        getattr(editor, "tree", None),
        background=LIST_BG,
        border=BORDER_PRESSED
    )


def build_scroll_frame_interface_editor_class(base_class):
    """Compatibility wrapper for older direct imports.

    Active UI composition installs the frames directly on the final editor
    instance and no longer adds this extra inheritance layer.
    """
    class ScrollFrameInterfaceEditor(base_class):

        def __init__(self, toolbox, parent=None):
            base_class.__init__(self, toolbox, parent)
            install_interface_editor_scroll_frames(self)

    ScrollFrameInterfaceEditor.__name__ = base_class.__name__
    return ScrollFrameInterfaceEditor


__all__ = [
    "build_scroll_frame_interface_editor_class",
    "install_interface_editor_scroll_frames",
]
