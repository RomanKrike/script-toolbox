# -*- coding: utf-8 -*-
from __future__ import print_function

from ..core.logging_utils import get_logger


_LOGGER = get_logger()
EVENT_SELECTION_CHANGED = "selection_changed"


class HostCallbackHandle(object):
    """Opaque, idempotent handle for one native host callback."""

    def __init__(
        self,
        event_name,
        native_handle,
        remover
    ):
        self.event_name = event_name
        self.native_handle = native_handle
        self._remover = remover
        self.active = True

    def close(self):
        if not self.active:
            return False

        remover = self._remover
        result = remover(
            self.native_handle
        )

        self.active = False
        self._remover = None
        return (
            True
            if result is None
            else bool(result)
        )


class HostCallbackGroup(object):
    """Own callback handles and release them together during UI teardown."""

    def __init__(
        self,
        host
    ):
        self.host = host
        self._handles = []

    @property
    def handles(self):
        return tuple(
            self._handles
        )

    def subscribe(
        self,
        event_name,
        callback
    ):
        handle = self.host.add_callback(
            event_name,
            callback
        )

        if handle is None:
            return False

        self._handles.append(
            handle
        )
        return True

    def clear(self):
        handles = list(
            self._handles
        )
        self._handles = []
        removed = 0

        for handle in reversed(handles):
            try:
                if self.host.remove_callback(
                    handle
                ):
                    removed += 1
            except Exception:
                # Host shutdown can invalidate native handles. Teardown remains
                # best-effort, but the failure is diagnostically important.
                _LOGGER.warning(
                    "Failed to remove host callback during teardown.",
                    exc_info=True
                )

        return removed

    def __len__(self):
        return len(
            self._handles
        )


__all__ = [
    "EVENT_SELECTION_CHANGED",
    "HostCallbackGroup",
    "HostCallbackHandle",
]
