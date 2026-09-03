# -*- coding: utf-8 -*-
from __future__ import print_function

import traceback

from ..compat import HOST


def execute_script(
    code,
    language="python",
    toolbox=None,
    parent=None
):
    code = code or ""
    language = (
        language or "python"
    ).lower()

    if not code.strip():
        return True

    try:
        if language == "python":
            namespace = {
                "__name__": "__script_toolbox_button__",
                "toolbox": toolbox,
            }
            namespace.update(
                HOST.script_namespace()
            )

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

        else:
            HOST.execute_native(
                language,
                code
            )

        return True

    except Exception:
        traceback.print_exc()

        try:
            from ..compat import QtGui

            QtGui.QMessageBox.critical(
                parent,
                "Script Toolbox",
                "Script execution failed. See the host Script Editor / console for traceback."
            )
        except Exception:
            pass

        return False
