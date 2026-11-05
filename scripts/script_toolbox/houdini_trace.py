# -*- coding: utf-8 -*-
"""Durable, best-effort breadcrumbs for a Houdini Python Panel crash."""
from __future__ import print_function

import os
import tempfile
import threading
import time


def log_path():
    directory = os.environ.get("SCRIPT_TOOLBOX_HOUDINI_TRACE_DIR")
    if not directory:
        directory = tempfile.gettempdir()
    return os.path.join(
        directory,
        "script-toolbox-houdini-pane-{0}.log".format(os.getpid())
    )


def trace(stage, detail=None):
    """Write one complete event and sync it before returning to Houdini."""
    try:
        path = log_path()
        directory = os.path.dirname(path)
        if not os.path.isdir(directory):
            try:
                os.makedirs(directory)
            except OSError:
                if not os.path.isdir(directory):
                    return
        line = "{0:.6f} pid={1} thread={2} {3}".format(
            time.time(), os.getpid(), threading.current_thread().ident, stage
        )
        if detail is not None:
            line += " {0!r}".format(detail)
        data = (line + "\n").encode("utf-8", "backslashreplace")
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            while data:
                data = data[os.write(fd, data):]
            os.fsync(fd)
        finally:
            os.close(fd)
    except Exception:
        # Diagnostic logging must never prevent the Python Panel from opening.
        pass
