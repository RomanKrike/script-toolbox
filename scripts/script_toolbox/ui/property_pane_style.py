# -*- coding: utf-8 -*-

from ..compat import QtGui
from ..style.palette import WINDOW_BG


PROPERTY_PANE_BACKGROUND = WINDOW_BG


def _apply_background(widget):
    if widget is None:
        return

    try:
        palette = widget.palette()
        color = QtGui.QColor(PROPERTY_PANE_BACKGROUND)
        palette.setColor(QtGui.QPalette.Window, color)
        palette.setColor(QtGui.QPalette.Base, color)
        widget.setPalette(palette)
        widget.setAutoFillBackground(True)
    except Exception:
        pass


def apply_property_pane_style(editor):
    """Apply the Qt4-safe Property Pane surface to one editor instance."""
    try:
        pane = editor.property_scroll.parentWidget()
        if pane is not None:
            pane.setObjectName("PropertyPane")
            _apply_background(pane)
    except Exception:
        pass

    try:
        _apply_background(editor.property_scroll)
        _apply_background(editor.property_scroll.viewport())
        _apply_background(editor.property_host)
    except Exception:
        pass


def install_property_pane_style(interface_editor_class, property_editor_class=None):
    """Compatibility installer for older direct imports.

    Active UI composition calls ``apply_property_pane_style`` directly and no
    longer patches the final InterfaceEditor class. PropertyEditorBase already
    applies the same shared background in its own constructor.
    """
    if getattr(interface_editor_class, "_property_pane_style_installed", False):
        return
    interface_editor_class._property_pane_style_installed = True

    original_build_ui = interface_editor_class.build_ui

    def build_ui(self):
        original_build_ui(self)
        apply_property_pane_style(self)

    interface_editor_class.build_ui = build_ui


__all__ = [
    "PROPERTY_PANE_BACKGROUND",
    "apply_property_pane_style",
    "install_property_pane_style",
]
