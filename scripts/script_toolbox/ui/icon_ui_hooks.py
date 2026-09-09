# -*- coding: utf-8 -*-
from __future__ import print_function

import os

from ..compat import QtGui
from ..pycompat import text_type
from ..style.builtin_icons import solar_icon_directory
from .icon_button import ICON_BUTTON_COMPACT
from .icon_button import create_icon_button


_INSTALLED_PROPERTY_BROWSE = False


def _dialog_path(value):
    if isinstance(value, (tuple, list)):
        if not value:
            return ""
        value = value[0]
    return text_type(value or "")


def _portable_icon_path(value):
    value = os.path.normpath(
        text_type(value or "")
    )
    if not value:
        return ""

    root = os.path.normcase(
        os.path.abspath(
            solar_icon_directory()
        )
    )
    parent = os.path.normcase(
        os.path.abspath(
            os.path.dirname(value)
        )
    )

    if parent == root:
        return "stsolar:{0}".format(
            os.path.basename(value)
        )

    return value


def _choose_icon_file(editor, line_edit):
    selected = QtGui.QFileDialog.getOpenFileName(
        editor,
        "Choose Icon",
        solar_icon_directory(),
        "Icon Files (*.svg *.png *.jpg *.jpeg *.ico);;All Files (*)"
    )
    selected = _dialog_path(selected)
    if not selected:
        return

    line_edit.setText(
        _portable_icon_path(selected)
    )

    try:
        editor._control_changed()
    except Exception:
        pass


def _install_browse_button(editor, line_edit):
    form = getattr(editor, "form", None)
    if form is None or line_edit is None:
        return None

    try:
        row, role = form.getWidgetPosition(line_edit)
    except Exception:
        return None

    if row < 0:
        return None

    container = QtGui.QWidget(editor)
    layout = QtGui.QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)

    try:
        form.removeWidget(line_edit)
    except Exception:
        pass

    line_edit.setParent(container)
    layout.addWidget(line_edit, 1)

    browse_button = create_icon_button(
        "folder-open",
        "Choose icon file",
        lambda: _choose_icon_file(
            editor,
            line_edit
        ),
        parent=container,
        preset=ICON_BUTTON_COMPACT
    )
    layout.addWidget(browse_button)

    form.setWidget(
        row,
        role,
        container
    )
    return browse_button


def install_property_icon_browse(
    button_editor_class,
    icon_editor_class
):
    global _INSTALLED_PROPERTY_BROWSE
    if _INSTALLED_PROPERTY_BROWSE:
        return

    original_button_init = button_editor_class.__init__

    def button_init(self, *args, **kwargs):
        original_button_init(self, *args, **kwargs)
        self.icon_browse_button = _install_browse_button(
            self,
            getattr(self, "icon_path", None)
        )

    button_editor_class.__init__ = button_init

    original_icon_init = icon_editor_class.__init__

    def selected_builtin_icon(self):
        return ""

    def refresh_icon_source(self):
        try:
            self.path.setEnabled(True)
        except Exception:
            pass

    icon_editor_class._selected_builtin_icon = selected_builtin_icon
    icon_editor_class._refresh_icon_source = refresh_icon_source

    def icon_init(self, *args, **kwargs):
        original_icon_init(self, *args, **kwargs)

        source = getattr(self, "icon_source", None)
        if source is not None:
            try:
                label = self.form.labelForField(source)
                if label is not None:
                    label.hide()
            except Exception:
                pass
            try:
                source.hide()
            except Exception:
                pass

        try:
            self.path.setEnabled(True)
        except Exception:
            pass

        self.icon_browse_button = _install_browse_button(
            self,
            getattr(self, "path", None)
        )

    icon_editor_class.__init__ = icon_init
    _INSTALLED_PROPERTY_BROWSE = True


def build_icon_interface_editor_class(base_class):
    """Compatibility shim retained for older direct imports.

    Share buttons now receive their final icons when they are created, so the
    former post-build icon discovery wrapper is no longer required.
    """
    return base_class


def install_script_editor_icons(script_editor_class):
    """Compatibility shim retained for older direct imports.

    ScriptEditorWidget now creates its clear-output button with the final icon
    directly, so UI copy is no longer used to identify that control.
    """
    return script_editor_class


__all__ = [
    "build_icon_interface_editor_class",
    "install_property_icon_browse",
    "install_script_editor_icons",
]
