# -*- coding: utf-8 -*-
from __future__ import print_function

import os

from .generic import DetectionOnlyAdapter


class MaxAdapter(DetectionOnlyAdapter):
    key = "3dsmax"
    display_name = "Autodesk 3ds Max"

    def install_patterns(self):
        if os.name != "nt":
            return []
        base = os.environ.get("ProgramFiles") or r"C:\Program Files"
        return [os.path.join(base, "Autodesk", "3ds Max *")]

    def user_config_path(self, version):
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        return os.path.join(
            base,
            "Autodesk",
            "3dsMax",
            version
        )


__all__ = ["MaxAdapter"]
