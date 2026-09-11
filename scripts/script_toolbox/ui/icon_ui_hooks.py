# -*- coding: utf-8 -*-
from __future__ import print_function



def install_property_icon_browse(
    button_editor_class,
    icon_editor_class
):
    """Compatibility shim retained for older direct imports.

    ButtonPropertyEditor and IconPropertyEditor now install their browse
    controls during normal construction, so no class monkeypatch is required.
    """
    return button_editor_class, icon_editor_class


def build_icon_interface_editor_class(base_class):
    """Compatibility shim retained for older direct imports.

    Share buttons receive their final icons when they are created, so the
    former post-build icon discovery wrapper is no longer required.
    """
    return base_class


def install_script_editor_icons(script_editor_class):
    """Compatibility shim retained for older direct imports.

    ScriptEditorWidget creates its clear-output button with the final icon
    directly, so UI copy is no longer used to identify that control.
    """
    return script_editor_class


__all__ = [
    "build_icon_interface_editor_class",
    "install_property_icon_browse",
    "install_script_editor_icons",
]
