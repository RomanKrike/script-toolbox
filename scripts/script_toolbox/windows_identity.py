# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

import os


APP_USER_MODEL_ID = "ScriptToolbox.App"


def apply_windows_app_user_model_id(app_id=APP_USER_MODEL_ID):
    """Apply the standalone Windows application identity to this process."""
    if os.name != "nt":
        return False

    try:
        import ctypes

        setter = ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID
        try:
            setter.argtypes = [
                ctypes.c_wchar_p,
            ]
            setter.restype = ctypes.c_long
        except Exception:
            pass

        return int(
            setter(
                app_id
            )
        ) >= 0
    except Exception:
        return False


__all__ = [
    "APP_USER_MODEL_ID",
    "apply_windows_app_user_model_id",
]
