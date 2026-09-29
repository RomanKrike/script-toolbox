# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import sys

from .generic import DetectionOnlyAdapter


class NukeAdapter(DetectionOnlyAdapter):
    key = "nuke"
    display_name = "Foundry Nuke"
    environment_variable = "NUKE_PATH"

    def install_patterns(self):
        if os.name == "nt":
            base = os.environ.get("ProgramFiles") or r"C:\Program Files"
            return [os.path.join(base, "Nuke*")]
        if sys.platform == "darwin":
            return ["/Applications/Nuke*.app"]
        return ["/usr/local/Nuke*"]

    def user_config_path(self, version):
        return os.path.expanduser("~/.nuke")


__all__ = ["NukeAdapter"]
