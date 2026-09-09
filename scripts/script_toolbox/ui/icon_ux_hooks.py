# -*- coding: utf-8 -*-
from __future__ import print_function

import os

from ..compat import QtCore
from ..compat import QtGui
from ..pycompat import text_type
from ..style import toolbar_icon
from .properties.button import ButtonPropertyEditor
from .properties.icon import IconPropertyEditor


_IMAGE_FILTER = (
    "Icon Files (*.png *.jpg *.jpeg *.bmp *.gif *.svg *.ico);;"
    "All Files (*)"
)


def icons_directory():
    return os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "icons"
        )
    )


def _asset_icon(name, fallback=None):
    path = os.path.join(
        icons_directory(),
        "{0}.svg".format(name)
    )
    icon = QtGui.QIcon(path)

    try:
        is_null = icon.isNull()
    except Exception:
        is_null = False

    if not is_null:
        return icon

    if fallback:
        return toolbar_icon(fallback)

    return QtGui.QIcon()


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


def _browse_icon(parent, line_edit):
    selected = QtGui.QFileDialog.getOpenFileName(
        parent,
        "Choose Icon",
        icons_directory(),
        _IMAGE_FILTER
    )
    selected = _dialog_path(selected)

    if not selected:
        return False

    line_edit.setText(selected)

    try:
        parent._control_changed()
    except Exception:
        pass

    return True


def _browse_button(parent, line_edit):
    button = QtGui.QToolButton()
    button.setObjectName("IconBrowseButton")
    button.setToolTip("Choose icon file")
    button.setFixedSize(26, 26)

    try:
        style = QtGui.QApplication.style()
        button.setIcon(
            style.standardIcon(
                QtGui.QStyle.SP_DirOpenIcon
            )
        )
    except Exception:
        pass

    button.clicked.connect(
        lambda: _browse_icon(parent, line_edit)
    )
    return button


def _install_browse_field(editor, line_edit):
    form = getattr(editor, "form", None)
    if form is None:
        return False

    try:
        row, role = form.getWidgetPosition(line_edit)
    except Exception:
        return False

    if row < 0:
        return False

    field = QtGui.QWidget()
    layout = QtGui.QHBoxLayout(field)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)

    try:
        form.removeWidget(line_edit)
    except Exception:
        pass

    layout.addWidget(line_edit, 1)
    layout.addWidget(
        _browse_button(editor, line_edit)
    )

    try:
        form.setWidget(
            row,
            QtGui.QFormLayout.FieldRole,
            field
        )
    except Exception:
        return False

    return True


def _wrap_property_init(editor_class, field_name):
    if getattr(
        editor_class,
        "_stb_icon_browse_installed",
        False
    ):
        return

    original_init = editor_class.__init__

    def wrapped_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        line_edit = getattr(self, field_name, None)
        if line_edit is not None:
            _install_browse_field(
                self,
                line_edit
            )

    editor_class.__init__ = wrapped_init
    editor_class._stb_icon_browse_installed = True


def install_property_icon_browse():
    _wrap_property_init(
        ButtonPropertyEditor,
        "icon_path"
    )
    _wrap_property_init(
        IconPropertyEditor,
        "path"
    )


def _find_tool_button(root, object_name=None, tooltip=None):
    try:
        buttons = root.findChildren(
            QtGui.QToolButton
        )
    except Exception:
        buttons = []

    for button in buttons:
        try:
            if (
                object_name is not None and
                text_type(button.objectName()) == object_name
            ):
                return button

            if (
                tooltip is not None and
                text_type(button.toolTip()) == tooltip
            ):
                return button
        except Exception:
            pass

    return None


def install_interface_share_icons(editor_class):
    if getattr(
        editor_class,
        "_stb_share_icons_installed",
        False
    ):
        return

    original_build_ui = editor_class.build_ui

    def build_ui(self):
        original_build_ui(self)

        paste_button = _find_tool_button(
            self,
            object_name="SharePasteButton"
        )
        if paste_button is not None:
            paste_button.setIcon(
                _asset_icon(
                    "cloud-download",
                    fallback="paste"
                )
            )

        share_button = _find_tool_button(
            self,
            object_name="ShareButton"
        )
        if share_button is not None:
            share_button.setIcon(
                _asset_icon(
                    "cloud-upload",
                    fallback="copy"
                )
            )

    editor_class.build_ui = build_ui
    editor_class._stb_share_icons_installed = True


def install_script_editor_clear_icon(editor_class):
    if getattr(
        editor_class,
        "_stb_clear_icon_installed",
        False
    ):
        return

    original_build_ui = editor_class.build_ui

    def build_ui(self):
        original_build_ui(self)
        button = _find_tool_button(
            self,
            tooltip="Clear Output"
        )
        if button is not None:
            button.setIcon(
                toolbar_icon("delete")
            )

    editor_class.build_ui = build_ui
    editor_class._stb_clear_icon_installed = True


def install_toolbox_settings_icon(toolbox_class):
    if getattr(
        toolbox_class,
        "_stb_settings_icon_installed",
        False
    ):
        return

    original_build_ui = toolbox_class.build_ui

    def build_ui(self):
        original_build_ui(self)
        button = _find_tool_button(
            self,
            tooltip="Edit Interface"
        )
        if button is not None:
            button.setIcon(
                _asset_icon(
                    "settings",
                    fallback="gear"
                )
            )

    toolbox_class.build_ui = build_ui
    toolbox_class._stb_settings_icon_installed = True


__all__ = [
    "icons_directory",
    "install_property_icon_browse",
    "install_interface_share_icons",
    "install_script_editor_clear_icon",
    "install_toolbox_settings_icon",
]
