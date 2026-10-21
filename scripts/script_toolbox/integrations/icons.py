# -*- coding: utf-8 -*-
from __future__ import print_function

import os

from .discovery import distribution_root


def integration_icon_path(distribution_path=None):
    """Return the shared PNG icon without importing a DCC or Qt binding."""
    return os.path.normpath(os.path.join(
        distribution_path or distribution_root(),
        "scripts", "script_toolbox", "resources", "logo_sbt.png"
    )).replace("\\", "/")
