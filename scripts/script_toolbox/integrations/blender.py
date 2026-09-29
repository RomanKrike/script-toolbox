# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import sys

from .generic import DetectionOnlyAdapter


class BlenderAdapter(DetectionOnlyAdapter):
    key = "blender"
    display_name = "Blender"

    def install_patterns(self):
        if os.name == "nt":
            base = os.environ.get("ProgramFiles") or r"C:\Program Files"
            return [os.path.join(base, "Blender Foundation", "Blender *")]
        if sys.platform == "darwin":
            return ["/Applications/Blender.app"]
        return ["/usr/bin/blender", "/opt/blender*"]

    def user_config_path(self, version):
        if os.name == "nt":
            base = os.environ.get("APPDATA") or os.path.expanduser("~")
            return os.path.join(
                base,
                "Blender Foundation",
                "Blender",
                version
            )
        if sys.platform == "darwin":
            return os.path.expanduser(
                "~/Library/Application Support/Blender/{0}".format(version)
            )
        return os.path.expanduser(
            "~/.config/blender/{0}".format(version)
        )


__all__ = ["BlenderAdapter"]
