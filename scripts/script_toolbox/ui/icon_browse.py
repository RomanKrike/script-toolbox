# -*- coding: utf-8 -*-
from __future__ import print_function

import os

from ..compat import QtGui
from ..pycompat import text_type
from ..style.builtin_icons import solar_icon_directory
from .icon_button import ICON_BUTTON_COMPACT
from .icon_button import create_icon_button
from .layout_helpers import configure_inline_layout


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


def choose_icon_file(editor, line_edit):
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


def install_icon_browse(editor, line_edit):
    """Place a compact Solar browse button beside an existing form field."""
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
    layout = configure_inline_layout(
        QtGui.QHBoxLayout(container)
    )

    try:
        form.removeWidget(line_edit)
    except Exception:
        pass

    line_edit.setParent(container)
    layout.addWidget(line_edit, 1)

    browse_button = create_icon_button(
        "folder-open",
        "Choose icon file",
        lambda: choose_icon_file(
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


__all__ = [
    "choose_icon_file",
    "install_icon_browse",
]
