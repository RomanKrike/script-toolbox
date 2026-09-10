# -*- coding: utf-8 -*-

PACKAGE_NAME = "script_toolbox"
DISPLAY_NAME = "Script Toolbox"
PLUGIN_VERSION = "0.9.1"

# Build metadata is stamped into Development packages by dev-build.yml.
# Source/stable builds intentionally keep these defaults.
BUILD_CHANNEL = "stable"
BUILD_NUMBER = 0
BUILD_COMMIT = ""

WINDOW_OBJECT_NAME = "MayaScriptToolbox"
EDITOR_OBJECT_NAME = "MayaScriptToolboxInterfaceEditor"

CONFIG_FILENAME = "maya_script_toolbox.json"
CONFIG_VERSION = 20

SETTINGS_FILENAME = "script_toolbox_settings.json"

GITHUB_REPOSITORY = "RomanKrike/script-toolbox"
GITHUB_TOKEN_ENV = "SCRIPT_TOOLBOX_GITHUB_TOKEN"
DEV_RELEASE_TAG = "dev-latest"

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
    "toggle_button",
    "icon",
    "toggle_icon",
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
    "column",
    "folder",
)
