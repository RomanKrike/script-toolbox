# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtGui


_INSTALL_MARKER = "_script_toolbox_runtime_pane_installed"


def _install_runtime_pane(toolbox):
    """Wrap ToolboxScroll in a stable, inset outer panel frame.

    QScrollArea owns its viewport and scrollbars, so using it as the visible
    frame can produce clipped or missing bottom/right border pixels in older
    Maya/Qt4 hosts. Keep the scroll area frameless and let a dedicated QFrame
    own the visible outline, matching the Interface Editor pane contract.

    RuntimePaneHost provides an external inset so the outline is visibly
    separated from the main-window edge instead of being painted flush against
    it, where Maya can make the border look missing.
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

    host = QtGui.QWidget(central)
    host.setObjectName("RuntimePaneHost")

    try:
        host.setSizePolicy(scroll.sizePolicy())
    except Exception:
        pass

    host_layout = QtGui.QVBoxLayout(host)
    host_layout.setContentsMargins(6, 6, 6, 6)
    host_layout.setSpacing(0)

    pane = QtGui.QFrame(host)
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
    host_layout.addWidget(pane)

    try:
        root.insertWidget(index, host, stretch)
    except Exception:
        root.insertWidget(index, host)

    toolbox.runtime_pane_host = host
    toolbox.runtime_pane = pane
    return pane


def _runtime_base_class(toolbox_class):
    """Return the canonical main_window.ScriptToolbox class from the MRO.

    The public runtime is instantiated from debounced_main_window.ScriptToolbox,
    while ui.__init__ also builds a decorated ScriptToolbox class. Patching only
    the decorated sibling does not affect the real window. Installing on the
    canonical base class makes every runtime subclass inherit the same build_ui
    wrapper.
    """
    try:
        mro = toolbox_class.__mro__
    except Exception:
        mro = (toolbox_class,)

    for candidate in mro:
        module_name = getattr(candidate, "__module__", "")
        class_name = getattr(candidate, "__name__", "")
        if (
            class_name == "ScriptToolbox" and
            module_name.endswith(".main_window")
        ):
            return candidate

    return toolbox_class


def install_runtime_pane(toolbox_class):
    """Install the runtime panel frame on the shared toolbox base class."""
    target_class = _runtime_base_class(toolbox_class)

    if getattr(target_class, _INSTALL_MARKER, False):
        return target_class

    original_build_ui = target_class.build_ui

    def build_ui(self):
        original_build_ui(self)
        _install_runtime_pane(self)

    target_class.build_ui = build_ui
    setattr(target_class, _INSTALL_MARKER, True)
    return target_class


__all__ = [
    "install_runtime_pane",
]
