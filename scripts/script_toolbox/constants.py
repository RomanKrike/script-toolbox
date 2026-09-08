# -*- coding: utf-8 -*-

PACKAGE_NAME = "script_toolbox"
DISPLAY_NAME = "Script Toolbox"
PLUGIN_VERSION = "0.8.5"

# Build metadata is stamped into Development packages by dev-build.yml.
# Source/stable builds intentionally keep these defaults.
BUILD_CHANNEL = "stable"
BUILD_NUMBER = 0
BUILD_COMMIT = ""

WINDOW_OBJECT_NAME = "MayaScriptToolbox"
EDITOR_OBJECT_NAME = "MayaScriptToolboxInterfaceEditor"

CONFIG_FILENAME = "maya_script_toolbox.json"
CONFIG_PATH_ENV = "SCRIPT_TOOLBOX_CONFIG_PATH"
CONFIG_VERSION = 18

SETTINGS_FILENAME = "script_toolbox_settings.json"
SETTINGS_PATH_ENV = "SCRIPT_TOOLBOX_SETTINGS_PATH"

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
    "icon",
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
