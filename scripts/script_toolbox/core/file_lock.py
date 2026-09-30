# -*- coding: utf-8 -*-
"""OS-owned locks. Files stay in place; a process crash releases the lock."""
from __future__ import print_function

import os
import threading

_GUARD = threading.Lock()
_LOCAL_LOCKS = {}


class FileLockError(RuntimeError):
    pass


class FileLock(object):
    def __init__(self, path, blocking=False):
        self.path = os.path.normcase(os.path.realpath(path))
        self.blocking = blocking
        self.handle = None
        with _GUARD:
            self.local = _LOCAL_LOCKS.setdefault(self.path, threading.Lock())

    def __enter__(self):
        if not self.local.acquire(self.blocking):
            raise FileLockError("Another operation already holds {0}".format(self.path))
        try:
            folder = os.path.dirname(self.path)
            if folder and not os.path.isdir(folder):
                try:
                    os.makedirs(folder)
                except OSError:
                    if not os.path.isdir(folder):
                        raise
            self.handle = open(self.path, "a+b")
            if os.path.getsize(self.path) == 0:
                self.handle.write(b"0")
                self.handle.flush()
            self.handle.seek(0)
            if os.name == "nt":
                import msvcrt
                mode = msvcrt.LK_LOCK if self.blocking else msvcrt.LK_NBLCK
                msvcrt.locking(self.handle.fileno(), mode, 1)
            else:
                import fcntl
                mode = fcntl.LOCK_EX
                if not self.blocking:
                    mode |= fcntl.LOCK_NB
                fcntl.flock(self.handle.fileno(), mode)
            return self
        except Exception as exc:
            if self.handle is not None:
                self.handle.close()
                self.handle = None
            self.local.release()
            raise FileLockError("Cannot acquire {0}: {1}".format(self.path, exc))

    def __exit__(self, *args):
        try:
            if self.handle is not None:
                if os.name == "nt":
                    import msvcrt
                    self.handle.seek(0)
                    msvcrt.locking(self.handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
                self.handle.close()
                self.handle = None
        finally:
            self.local.release()


def installation_lock(root):
    return FileLock(os.path.join(root, ".script_toolbox_update.lock"))
