# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

import sys

from .windows_identity import apply_windows_app_user_model_id


def application_arguments(argv=None):
    """Return argv in the form expected by QApplication."""
    if argv is None:
        return list(
            sys.argv
        )

    return list(
        argv
    )


def exec_application(application):
    """Run the Qt event loop across Qt4/Qt5/Qt6 API variants."""
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


def run_standalone(
    application_class,
    show_toolbox,
    argv=None
):
    """Create the standalone QApplication and show the normal toolbox UI."""
    apply_windows_app_user_model_id()

    application = application_class.instance()
    owns_application = application is None

    if application is None:
        application = application_class(
            application_arguments(
                argv
            )
        )

    set_window_icon = getattr(
        application,
        "setWindowIcon",
        None
    )
    if set_window_icon is not None:
        try:
            from .style import application_icon
            icon = application_icon()
            if not icon.isNull():
                set_window_icon(
                    icon
                )
        except Exception:
            pass

    show_toolbox()

    if not owns_application:
        return 0

    return exec_application(
        application
    )


def main(argv=None):
    """Run Script Toolbox as the explicit standalone host."""
    from .compat import HOST
    from .compat import QtGui

    if HOST.key != "standalone":
        raise RuntimeError(
            "Standalone entry point cannot run inside the {0} host.".format(
                HOST.display_name
            )
        )

    def _show_toolbox():
        # Keep UI imports behind QApplication creation. The toolbox itself is
        # still the exact same bootstrap and widget tree used by DCC hosts.
        from .bootstrap import show
        window = show()
        from .core.restart_ack import acknowledge_restart
        acknowledge_restart()
        return window

    return run_standalone(
        QtGui.QApplication,
        _show_toolbox,
        argv=argv
    )


if __name__ == "__main__":
    sys.exit(
        main()
    )


__all__ = [
    "application_arguments",
    "exec_application",
    "main",
    "run_standalone",
]
