# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import sys

from .generic import DetectionOnlyAdapter
from .discovery import windows_documents_dir


class HoudiniAdapter(DetectionOnlyAdapter):
    key = "houdini"
    display_name = "SideFX Houdini"
    environment_variable = "HFS"

    def install_patterns(self):
        if os.name == "nt":
            base = os.environ.get("ProgramFiles") or r"C:\Program Files"
            return [os.path.join(base, "Side Effects Software", "Houdini *")]
        if sys.platform == "darwin":
            return ["/Applications/Houdini/Houdini*.app"]
        return ["/opt/hfs*"]

    def user_config_path(self, version):
        if os.name == "nt":
            return os.path.join(
                windows_documents_dir(),
                "houdini{0}".format(version)
            )
        return os.path.expanduser(
            "~/houdini{0}".format(version)
        )


__all__ = ["HoudiniAdapter"]
