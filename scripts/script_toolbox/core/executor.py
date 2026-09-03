# -*- coding: utf-8 -*-
from __future__ import print_function

import traceback

from ..compat import cmds
from ..compat import mel


def execute_script(
    code,
    language="python",
    toolbox=None,
    parent=None
):
    code = code or ""

    if not code.strip():
        return True

    try:
        if language == "mel":
            mel.eval(code)
        else:
            namespace = {
                "__name__": "__script_toolbox_button__",
                "cmds": cmds,
                "mel": mel,
                "toolbox": toolbox,
            }

            compiled = compile(
                code,
                "<Script Toolbox>",
                "exec"
            )
            eval(
                compiled,
                namespace,
                namespace
            )

        return True

    except Exception:
        traceback.print_exc()

        try:
            from ..compat import QtGui

            QtGui.QMessageBox.critical(
                parent,
                "Script Toolbox",
                "Script execution failed. See Script Editor for traceback."
            )
        except Exception:
            pass

        return False
