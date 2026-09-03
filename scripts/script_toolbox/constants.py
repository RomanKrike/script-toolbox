# -*- coding: utf-8 -*-

PACKAGE_NAME = "script_toolbox"
DISPLAY_NAME = "Script Toolbox"

WINDOW_OBJECT_NAME = "MayaScriptToolbox"
EDITOR_OBJECT_NAME = "MayaScriptToolboxInterfaceEditor"

CONFIG_FILENAME = "maya_script_toolbox.json"
CONFIG_VERSION = 15

SUPPORTED_LANGUAGES = (
    "python",
    "mel",
)

FOLDER_TYPES = (
    "collapsible",
    "simple",
    "tabs",
    "radio",
)

ITEM_KINDS = (
    "button",
    "string",
    "integer",
    "float",
    "checkbox",
    "menu",
    "color",
    "field",
    "label",
    "separator",
    "row",
    "folder",
)
