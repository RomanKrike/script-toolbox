# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import json
import sys
import traceback


def repository_root():
    return os.path.dirname(
        os.path.dirname(
            os.path.abspath(
                __file__
            )
        )
    )


def install_source_path():
    scripts_path = os.path.join(
        repository_root(),
        "scripts"
    )

    if scripts_path not in sys.path:
        sys.path.insert(
            0,
            scripts_path
        )

    return scripts_path


def show_startup_error(message):
    """Best-effort error surface for the windowed portable launcher."""
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(
            None,
            message,
            u"Script Toolbox - Startup Error",
            0x00000010
        )
        return True
    except Exception:
        return False


def main():
    status_path = os.path.join(repository_root(), "standalone-update-status.json")
    if os.path.isfile(status_path):
        try:
            with open(status_path, "r") as handle:
                status = json.load(handle)
            if status.get("state") in ("failed", "recovered", "recovery_required", "cancelled"):
                show_startup_error(u"Portable update: {0}\n\n{1}\n\nDetails: {2}".format(
                    status.get("state"), status.get("message", ""), status_path))
        except Exception:
            pass
    install_source_path()

    try:
        from script_toolbox.standalone import main as standalone_main
        return standalone_main()
    except Exception:
        diagnostic = traceback.format_exc()

        try:
            sys.stderr.write(
                diagnostic
            )
        except Exception:
            pass

        show_startup_error(
            u"Script Toolbox could not start.\n\n{0}".format(
                diagnostic
            )
        )
        return 1


if __name__ == "__main__":
    sys.exit(
        main()
    )
