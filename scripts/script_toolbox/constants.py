# -*- coding: utf-8 -*-

PACKAGE_NAME = "script_toolbox"
DISPLAY_NAME = "Script Toolbox"
PLUGIN_VERSION = "0.4.4"

WINDOW_OBJECT_NAME = "MayaScriptToolbox"
EDITOR_OBJECT_NAME = "MayaScriptToolboxInterfaceEditor"

CONFIG_FILENAME = "maya_script_toolbox.json"
CONFIG_PATH_ENV = "SCRIPT_TOOLBOX_CONFIG_PATH"
CONFIG_VERSION = 16

GITHUB_REPOSITORY = "RomanKrike/script-toolbox"
GITHUB_TOKEN_ENV = "SCRIPT_TOOLBOX_GITHUB_TOKEN"

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
