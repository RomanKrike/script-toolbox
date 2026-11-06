# -*- coding: utf-8 -*-
"""Durable, best-effort breadcrumbs for a Houdini Python Panel crash."""
from __future__ import print_function

import os
import tempfile
import threading
import time


_HANG_TIMEOUT_SECONDS = 10
_hang_log = None
_hang_timer = None
_last_heartbeat = None
_crash_log = None
_gc_frozen_once = False


def freeze_initial_gc_objects():
    """Exclude objects present at first pane creation from later GC passes."""
    global _gc_frozen_once
    if _gc_frozen_once:
        return True
    import gc
    freeze = getattr(gc, "freeze", None)
    get_count = getattr(gc, "get_freeze_count", None)
    if freeze is None or get_count is None:
        trace("gc.freeze_unavailable")
        return False
    before = get_count()
    trace("gc.freeze_begin", "tracked={0} count={1!r}".format(
        len(gc.get_objects()), gc.get_count()
    ))
    try:
        freeze()
    except Exception:
        import traceback
        trace("gc.freeze_error", traceback.format_exc())
        return False
    trace("gc.freeze_done", "frozen={0} total={1}".format(
        get_count() - before, get_count()
    ))
    _gc_frozen_once = True
    return True


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


def _refresh_hang_watchdog():
    global _last_heartbeat
    import faulthandler

    now = time.time()
    if _last_heartbeat is not None:
        gap = now - _last_heartbeat
        if gap >= _HANG_TIMEOUT_SECONDS:
            trace("watchdog.event_loop_resumed", gap)
    faulthandler.cancel_dump_traceback_later()
    faulthandler.dump_traceback_later(
        _HANG_TIMEOUT_SECONDS, repeat=True, file=_hang_log
    )
    _last_heartbeat = now


def enable_crash_trace():
    """Capture a Python stack if a native fault reaches Python's handler."""
    global _crash_log
    if _crash_log is not None:
        return True
    handle = None
    try:
        import faulthandler
        if faulthandler.is_enabled():
            trace("crash_handler.already_enabled")
            return False
        handle = open(log_path(), "ab", 0)
        faulthandler.enable(file=handle, all_threads=True)
        _crash_log = handle
        trace("crash_handler.armed")
        return True
    except Exception:
        if handle is not None:
            handle.close()
        import traceback
        trace("crash_handler.error", traceback.format_exc())
        return False


def start_hang_watchdog(qt_core, application):
    """Dump Python stacks if Houdini's Qt event loop stops for ten seconds."""
    global _hang_log, _hang_timer
    if _hang_timer is not None:
        return True
    enable_crash_trace()
    try:
        handle = open(log_path(), "ab", 0)
        _hang_log = handle
        timer = qt_core.QTimer(application)
        timer.setInterval(1000)
        timer.timeout.connect(_refresh_hang_watchdog)
        _refresh_hang_watchdog()
        timer.start()
        _hang_timer = timer
        trace("watchdog.armed")
        return True
    except Exception:
        import traceback
        trace("watchdog.error", traceback.format_exc())
        try:
            import faulthandler
            faulthandler.cancel_dump_traceback_later()
        except Exception:
            pass
        if _hang_log is not None:
            _hang_log.close()
            _hang_log = None
        return False
