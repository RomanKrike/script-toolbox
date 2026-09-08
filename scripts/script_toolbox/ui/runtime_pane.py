# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtGui


_INSTALLED = False


def _install_runtime_pane(toolbox):
    """Wrap ToolboxScroll in a stable outer panel frame.

    QScrollArea owns its viewport and scrollbars, so using it as the visible
    frame can produce clipped or missing bottom/right border pixels in older
    Maya/Qt4 hosts. Keep the scroll area frameless and let a sibling QFrame
    own the visible outline, matching the Interface Editor pane contract.
    """
    if getattr(toolbox, "runtime_pane", None) is not None:
        return toolbox.runtime_pane

    scroll = getattr(toolbox, "scroll", None)
    central = toolbox.centralWidget()
    root = central.layout() if central is not None else None

    if scroll is None or root is None:
        return None

    try:
        index = root.indexOf(scroll)
    except Exception:
        index = -1

    if index < 0:
        return None

    try:
        stretch = root.stretch(index)
    except Exception:
        stretch = 1

    pane = QtGui.QFrame(central)
    pane.setObjectName("RuntimePane")

    try:
        pane.setSizePolicy(scroll.sizePolicy())
    except Exception:
        pass

    pane_layout = QtGui.QVBoxLayout(pane)
    pane_layout.setContentsMargins(2, 2, 2, 2)
    pane_layout.setSpacing(0)

    root.removeWidget(scroll)
    scroll.setParent(pane)
    pane_layout.addWidget(scroll)

    try:
        root.insertWidget(index, pane, stretch)
    except Exception:
        root.insertWidget(index, pane)

    toolbox.runtime_pane = pane
    return pane


def install_runtime_pane(toolbox_class):
    """Install the runtime panel frame without changing ScriptToolbox API."""
    global _INSTALLED
    if _INSTALLED:
        return

    original_build_ui = toolbox_class.build_ui

    def build_ui(self):
        original_build_ui(self)
        _install_runtime_pane(self)

    toolbox_class.build_ui = build_ui
    _INSTALLED = True


__all__ = [
    "install_runtime_pane",
]
