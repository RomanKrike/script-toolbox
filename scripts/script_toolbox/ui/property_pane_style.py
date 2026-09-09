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


def install_property_pane_style(interface_editor_class, property_editor_class):
    """Keep Parameter Description on the same dark surface as the dialog.

    Maya 2015 / Qt4 is inconsistent about QScrollArea viewport QSS, so the
    property pane needs both a late stylesheet override and an explicit
    palette fallback. Patch the final editor class so this also survives the
    layout/document/view-state wrappers installed by ``ui.__init__``.
    """
    if getattr(interface_editor_class, "_property_pane_style_installed", False):
        return
    interface_editor_class._property_pane_style_installed = True

    original_build_ui = interface_editor_class.build_ui

    def build_ui(self):
        original_build_ui(self)

        try:
            pane = self.property_scroll.parentWidget()
            if pane is not None:
                pane.setObjectName("PropertyPane")
                _apply_background(pane)
        except Exception:
            pass

        try:
            _apply_background(self.property_scroll)
            _apply_background(self.property_scroll.viewport())
            _apply_background(self.property_host)
        except Exception:
            pass

    interface_editor_class.build_ui = build_ui

    if getattr(property_editor_class, "_property_pane_style_installed", False):
        return
    property_editor_class._property_pane_style_installed = True

    original_property_init = property_editor_class.__init__

    def property_editor_init(self, *args, **kwargs):
        original_property_init(self, *args, **kwargs)
        _apply_background(self)

    property_editor_class.__init__ = property_editor_init


__all__ = [
    "PROPERTY_PANE_BACKGROUND",
    "install_property_pane_style",
]
