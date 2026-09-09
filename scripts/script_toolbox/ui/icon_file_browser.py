# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtGui
from ..pycompat import text_type
from ..style.builtin_icons import builtin_icon_resource_from_file_path
from ..style.builtin_icons import builtin_icons_directory


_IMAGE_FILTER = (
    "Icon Files (*.svg *.png *.jpg *.jpeg *.bmp *.gif *.ico);;"
    "All Files (*)"
)


def _dialog_path(value):
    if isinstance(value, (tuple, list)):
        if not value:
            return ""
        value = value[0]

    try:
        value = value.toString()
    except Exception:
        pass

    return text_type(value or "")


def browse_icon_file(parent, line_edit):
    selected = QtGui.QFileDialog.getOpenFileName(
        parent,
        "Choose Icon",
        builtin_icons_directory(),
        _IMAGE_FILTER
    )
    selected = _dialog_path(selected)

    if not selected:
        return False

    portable = builtin_icon_resource_from_file_path(
        selected
    )
    line_edit.setText(
        portable or selected
    )

    try:
        parent._control_changed()
    except Exception:
        pass

    return True


def icon_browse_button(parent, line_edit):
    button = QtGui.QToolButton()
    button.setObjectName("IconBrowseButton")
    button.setToolTip("Choose icon file")
    button.setFixedSize(26, 26)

    try:
        button.setIcon(
            QtGui.QApplication.style().standardIcon(
                QtGui.QStyle.SP_DirOpenIcon
            )
        )
    except Exception:
        pass

    button.clicked.connect(
        lambda: browse_icon_file(
            parent,
            line_edit
        )
    )
    return button


def icon_path_field(parent, line_edit):
    field = QtGui.QWidget()
    layout = QtGui.QHBoxLayout(field)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    layout.addWidget(line_edit, 1)
    layout.addWidget(
        icon_browse_button(
            parent,
            line_edit
        )
    )
    return field


def install_icon_path_browse(editor_class, field_name):
    """Wrap an existing QFormLayout path field with a Browse button."""
    marker = "_stb_icon_path_browse_{0}".format(
        field_name
    )
    if getattr(editor_class, marker, False):
        return

    original_init = editor_class.__init__

    def wrapped_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)

        line_edit = getattr(
            self,
            field_name,
            None
        )
        form = getattr(
            self,
            "form",
            None
        )
        if line_edit is None or form is None:
            return

        try:
            row, role = form.getWidgetPosition(
                line_edit
            )
        except Exception:
            return

        if row < 0:
            return

        try:
            form.removeWidget(line_edit)
            form.setWidget(
                row,
                QtGui.QFormLayout.FieldRole,
                icon_path_field(
                    self,
                    line_edit
                )
            )
        except Exception:
            return

    editor_class.__init__ = wrapped_init
    setattr(
        editor_class,
        marker,
        True
    )


__all__ = [
    "browse_icon_file",
    "icon_browse_button",
    "icon_path_field",
    "install_icon_path_browse",
]
