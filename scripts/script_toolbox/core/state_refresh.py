# -*- coding: utf-8 -*-
from __future__ import print_function


class StateRefreshQueue(object):
    """Track whether a full state-button refresh is already scheduled.

    The queue owns no timer and no Qt objects. ``request()`` returns True only
    for the first request in a coalescing window, which lets the UI start one
    timer without restarting it for every value/selection event.
    """

    def __init__(self):
        self.pending = False

    def request(self):
        if self.pending:
            return False

        self.pending = True
        return True

    def consume(self):
        if not self.pending:
            return False

        self.pending = False
        return True

    def cancel(self):
        was_pending = self.pending
        self.pending = False
        return was_pending


__all__ = [
    "StateRefreshQueue",
]
