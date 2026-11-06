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
_gc_quarantined_once = False


def quarantine_gc_cycles():
    """Keep one batch of unreachable objects for first-pane fault diagnosis."""
    global _gc_quarantined_once
    if _gc_quarantined_once:
        return True
    import gc
    previous_flags = gc.get_debug()
    first = len(gc.garbage)
    try:
        gc.set_debug(previous_flags | gc.DEBUG_SAVEALL)
        unreachable = gc.collect()
    except Exception:
        import traceback
        trace("gc.quarantine_error", traceback.format_exc())
        return False
    finally:
        gc.set_debug(previous_flags)
    counts = {}
    for obj in gc.garbage[first:]:
        cls = type(obj)
        name = "{0}.{1}".format(cls.__module__, cls.__name__)
        counts[name] = counts.get(name, 0) + 1
    top = sorted(counts.items(), key=lambda entry: (-entry[1], entry[0]))[:12]
    trace("gc.quarantined", "unreachable={0} retained={1} types={2!r}".format(
        unreachable, len(gc.garbage) - first, top
    ))
    _gc_quarantined_once = True
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
