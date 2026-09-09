# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtGui
from ..pycompat import text_type
from ..style import toolbar_icon


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
    marker = "_stb_share_icon_overrides_installed"
    if getattr(editor_class, marker, False):
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
                toolbar_icon("cloud-download")
            )

        share_button = _find_tool_button(
            self,
            object_name="ShareButton"
        )
        if share_button is not None:
            share_button.setIcon(
                toolbar_icon("cloud-upload")
            )

    editor_class.build_ui = build_ui
    setattr(editor_class, marker, True)


def install_script_editor_clear_icon(editor_class):
    marker = "_stb_clear_icon_override_installed"
    if getattr(editor_class, marker, False):
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
    setattr(editor_class, marker, True)


def install_toolbox_settings_icon(toolbox_class):
    marker = "_stb_settings_icon_override_installed"
    if getattr(toolbox_class, marker, False):
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
                toolbar_icon("settings")
            )

    toolbox_class.build_ui = build_ui
    setattr(toolbox_class, marker, True)


__all__ = [
    "install_interface_share_icons",
    "install_script_editor_clear_icon",
    "install_toolbox_settings_icon",
]
