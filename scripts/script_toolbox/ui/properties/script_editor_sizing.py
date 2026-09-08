# -*- coding: utf-8 -*-

from ...compat import QtGui
from . import base as base_module
from . import bindings as bindings_module


_INSTALLED = False


def install_expanding_script_editors():
    """Give property script editors a useful minimum and vertical growth.

    Property editors live in a resizable QScrollArea.  The legacy layout kept
    the Triggers group at its sizeHint, so extra dialog height could end up as
    unused space instead of growing the code editor.  Keep the property fields
    compact and assign the remaining vertical space to Triggers.
    """
    global _INSTALLED
    if _INSTALLED:
        return
    _INSTALLED = True

    original_page_init = bindings_module.BindingPage.__init__

    def binding_page_init(self, *args, **kwargs):
        original_page_init(self, *args, **kwargs)

        if self.script_editor is None:
            return

        self.script_editor.setMinimumHeight(240)
        try:
            self.script_editor.setSizePolicy(
                QtGui.QSizePolicy.Expanding,
                QtGui.QSizePolicy.Expanding
            )
        except Exception:
            pass

    bindings_module.BindingPage.__init__ = binding_page_init

    original_property_init = base_module.PropertyEditorBase.__init__

    def property_editor_init(self, *args, **kwargs):
        original_property_init(self, *args, **kwargs)

        try:
            self.setSizePolicy(
                QtGui.QSizePolicy.Expanding,
                QtGui.QSizePolicy.Expanding
            )
        except Exception:
            pass

        try:
            index = self.root_layout.indexOf(
                self.binding_panel
            )
            if index >= 0:
                self.root_layout.setStretch(
                    index,
                    1
                )
        except Exception:
            pass

        try:
            self.binding_panel.setSizePolicy(
                QtGui.QSizePolicy.Expanding,
                QtGui.QSizePolicy.Expanding
            )
        except Exception:
            pass

    base_module.PropertyEditorBase.__init__ = property_editor_init


__all__ = [
    "install_expanding_script_editors",
]
