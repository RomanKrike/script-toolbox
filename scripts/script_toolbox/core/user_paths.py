# -*- coding: utf-8 -*-
from __future__ import print_function

import os

from ..constants import CONFIG_FILENAME
from ..constants import SETTINGS_FILENAME
from ..hosts import HOST


def user_config_dir():
    """Return the single host-specific Script Toolbox user config directory."""
    try:
        folder = HOST.user_config_dir()
    except Exception:
        folder = os.path.expanduser("~")

    return os.path.normpath(
        folder
    )


def config_path():
    """Return the canonical toolbox document path for the active host."""
    try:
        filename = HOST.config_filename()
    except Exception:
        filename = CONFIG_FILENAME

    return os.path.normpath(
        os.path.join(
            user_config_dir(),
            filename
        )
    )


def settings_path():
    """Return the canonical Script Toolbox preferences path."""
    return os.path.normpath(
        os.path.join(
            user_config_dir(),
            SETTINGS_FILENAME
        )
    )


__all__ = [
    "config_path",
    "settings_path",
    "user_config_dir",
]
