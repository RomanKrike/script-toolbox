# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import sys
import traceback


def _exec_application(application):
    callback = getattr(
        application,
        "exec_",
        None
    )
    if callback is None:
        callback = getattr(
            application,
            "exec"
        )
    return int(
        callback()
    )


def main():
    root = os.environ.get(
        "SCRIPT_TOOLBOX_PORTABLE_ROOT",
        ""
    )
    if not root:
        raise RuntimeError(
            "SCRIPT_TOOLBOX_PORTABLE_ROOT is required."
        )

    scripts_path = os.path.join(
        root,
        "scripts"
    )
    sys.path.insert(
        0,
        scripts_path
    )

    import script_toolbox
    from script_toolbox.compat import QtCore
    from script_toolbox.compat import QtGui
    from script_toolbox.style import STYLE

    if script_toolbox.__host__ != "standalone":
        raise RuntimeError(
            "Expected standalone host, got {0}.".format(
                script_toolbox.__host__
            )
        )

    application = QtGui.QApplication.instance()
    if application is None:
        application = QtGui.QApplication(
            []
        )

    try:
        application.setQuitOnLastWindowClosed(
            True
        )
    except Exception:
        pass

    state = {
        "completed": False,
        "error": None,
        "window": None,
    }

    window = script_toolbox.show()
    if window is None or not window.isVisible():
        raise RuntimeError(
            "Main standalone window did not open."
        )

    if window.windowIcon().isNull():
        raise RuntimeError(
            "Main standalone window has no Script Toolbox icon."
        )

    menu = getattr(
        window,
        "settings_menu",
        None
    )
    if menu is None:
        raise RuntimeError(
            "Header settings menu was not created."
        )
    if menu.styleSheet() != STYLE:
        raise RuntimeError(
            "Header settings menu does not use the Script Toolbox stylesheet."
        )

    window.open_interface_editor()
    editor = window.editor_window
    if editor is None or not editor.isVisible():
        raise RuntimeError(
            "Interface Editor did not open."
        )
    if editor.windowIcon().isNull():
        raise RuntimeError(
            "Interface Editor has no Script Toolbox icon."
        )
    editor.close()

    def fail():
        try:
            state["error"] = traceback.format_exc()
        except Exception:
            state["error"] = "Standalone smoke failed."
        application.exit(
            1
        )

    def finish():
        try:
            reloaded = state.get(
                "window"
            )
            if reloaded is None or not reloaded.isVisible():
                raise RuntimeError(
                    "Standalone window did not reopen after hot reload."
                )

            if reloaded.windowIcon().isNull():
                raise RuntimeError(
                    "Reloaded standalone window lost the Script Toolbox icon."
                )

            menu = getattr(
                reloaded,
                "settings_menu",
                None
            )
            if menu is None or menu.styleSheet() != STYLE:
                raise RuntimeError(
                    "Reloaded settings menu lost the Script Toolbox stylesheet."
                )

            state["completed"] = True
            reloaded.close()
            application.quit()
        except Exception:
            fail()

    def reload_window():
        try:
            from script_toolbox.bootstrap import hot_reload_toolbox

            state["window"] = hot_reload_toolbox()
            QtCore.QTimer.singleShot(
                50,
                finish
            )
        except Exception:
            fail()

    QtCore.QTimer.singleShot(
        0,
        reload_window
    )

    result = _exec_application(
        application
    )

    if state["error"]:
        raise RuntimeError(
            state["error"]
        )
    if not state["completed"]:
        raise RuntimeError(
            "Qt event loop exited before standalone hot reload completed."
        )
    if result not in (
        0,
        1,
    ):
        raise RuntimeError(
            "Unexpected Qt event-loop result: {0}".format(
                result
            )
        )

    print(
        "Standalone UI/editor/menu/icon/update smoke passed"
    )
    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )
