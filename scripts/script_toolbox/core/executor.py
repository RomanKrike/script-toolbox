# -*- coding: utf-8 -*-
from __future__ import print_function

import traceback

from ..hosts import HOST
from .source import prepare_python_source


def _script_namespace(toolbox=None, extra_namespace=None):
    namespace = {
        "__name__": "__script_toolbox_button__",
        "toolbox": toolbox,
    }
    namespace.update(
        HOST.script_namespace()
    )

    if extra_namespace:
        namespace.update(
            extra_namespace
        )

    return namespace


def execute_script(
    code,
    language="python",
    toolbox=None,
    parent=None,
    extra_namespace=None
):
    code = code or ""
    language = (
        language or "python"
    ).lower()

    if not code.strip():
        return True

    try:
        if language == "python":
            namespace = _script_namespace(
                toolbox=toolbox,
                extra_namespace=extra_namespace
            )

            compiled = compile(
                prepare_python_source(
                    code
                ),
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


def evaluate_python_state(
    code,
    toolbox=None,
    parent=None
):
    """Execute a state query script and return its boolean ``state`` value.

    State scripts set ``state = True`` or ``state = False``. An empty script
    resolves to False. Errors are reported through the same host UI path as
    normal button execution.
    """
    code = code or ""

    if not code.strip():
        return False

    namespace = _script_namespace(
        toolbox=toolbox,
        extra_namespace={
            "state": False,
        }
    )

    try:
        compiled = compile(
            prepare_python_source(
                code
            ),
            "<Script Toolbox State>",
            "exec"
        )
        eval(
            compiled,
            namespace,
            namespace
        )
        return bool(
            namespace.get(
                "state",
                False
            )
        )

    except Exception:
        traceback.print_exc()

        try:
            from ..compat import QtGui

            QtGui.QMessageBox.critical(
                parent,
                "Script Toolbox",
                "State query failed. See the host Script Editor / console for traceback."
            )
        except Exception:
            pass

        return None


__all__ = [
    "evaluate_python_state",
    "execute_script",
]
