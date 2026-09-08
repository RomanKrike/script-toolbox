# -*- coding: utf-8 -*-
from __future__ import print_function

from .scroll_surface_frames import wrap_scroll_widget


def build_scroll_frame_interface_editor_class(base_class):
    """Apply the shared scroll-surface frame to both editor trees.

    Editor trees use the #242424 tree surface and the historical #161616
    outline, but the geometry contract is identical to runtime lists and text
    editors: the visible border belongs to a parent frame, never to the
    QAbstractScrollArea that owns the scrollbars.
    """
    class ScrollFrameInterfaceEditor(base_class):

        def __init__(self, toolbox, parent=None):
            base_class.__init__(self, toolbox, parent)
            self.palette_scroll_frame = wrap_scroll_widget(
                getattr(self, "palette", None),
                background="#242424",
                border="#161616"
            )
            self.tree_scroll_frame = wrap_scroll_widget(
                getattr(self, "tree", None),
                background="#242424",
                border="#161616"
            )

    ScrollFrameInterfaceEditor.__name__ = base_class.__name__
    return ScrollFrameInterfaceEditor


__all__ = ["build_scroll_frame_interface_editor_class"]
