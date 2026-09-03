# -*- coding: utf-8 -*-
from __future__ import print_function

import maya.cmds as cmds
import maya.mel as mel

from .base import BaseHost


class MayaHost(BaseHost):

    key = "maya"
    display_name = "Maya"
    selection_noun = "Maya objects"

    def app_version(self):
        try:
            return str(
                cmds.about(
                    version=True
                )
            )
        except Exception:
            return ""

    def current_selection(
        self,
        long_names=True
    ):
        return cmds.ls(
            selection=True,
            long=bool(
                long_names
            )
        ) or []

    def object_exists(
        self,
        name
    ):
        try:
            return bool(
                cmds.objExists(
                    name
                )
            )
        except Exception:
            return False

    def select_objects(
        self,
        names
    ):
        try:
            cmds.select(
                names,
                replace=True
            )
            return True
        except Exception:
            return False

    def available_languages(self):
        return (
            "python",
            "mel",
        )

    def script_namespace(self):
        return {
            "host": self,
            "cmds": cmds,
            "mel": mel,
        }

    def execute_native(
        self,
        language,
        code
    ):
        if language == "mel":
            return mel.eval(
                code
            )

        return BaseHost.execute_native(
            self,
            language,
            code
        )

    def user_config_dir(self):
        try:
            return cmds.internalVar(
                userPrefDir=True
            )
        except Exception:
            return BaseHost.user_config_dir(
                self
            )

    def config_filename(self):
        return "maya_script_toolbox.json"

    def shift_pressed_native(self):
        try:
            return bool(
                cmds.getModifiers() &
                1
            )
        except Exception:
            return False


__all__ = [
    "MayaHost",
]
