# -*- coding: utf-8 -*-
from __future__ import print_function

import os

from .discovery import distribution_root


def maya_shelf_icon_path(distribution_path=None):
    """Return the native 32 px shelf image; large originals inflate Maya buttons."""
    return os.path.join(os.path.dirname(integration_icon_path(distribution_path)),
                        "logo_sbt_shelf_32.png").replace("\\", "/")


def integration_icon_path(distribution_path=None):
    """Return the shared PNG icon without importing a DCC or Qt binding."""
    return os.path.normpath(os.path.join(
        distribution_path or distribution_root(),
        "scripts", "script_toolbox", "resources", "logo_sbt.png"
    )).replace("\\", "/")
