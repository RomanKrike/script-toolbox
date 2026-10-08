# -*- coding: utf-8 -*-
"""GUI-owned delivery of filesystem-only snapshot jobs."""
from __future__ import print_function

from ..compat import QtCore
from ..core.preset_references import load_preset_snapshot, snapshot_cache_tokens
from ..pycompat import text_type
from .managed_presets import BackgroundJob


class SnapshotLoader(QtCore.QObject):
    def __init__(self, owner, registry):
        QtCore.QObject.__init__(self, owner)
        self.registry = registry
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(25)
        self.timer.timeout.connect(self.poll)
        self.job = None
        self.pending = None
        self.generation = 0
        self.busy = False
        self.closed = False

    def request(self, callback, previous=None):
        if self.closed:
            return
        self.generation += 1
        self.pending = (self.generation, callback, previous)
        self.busy = True
        if self.job is None:
            self._start()

    def _start(self):
        generation, callback, previous = self.pending
        self.pending = None
        registry = self.registry
        # No QWidget, QObject or bound GUI callback is captured by this action.
        self.job = (generation, callback, previous,
                    BackgroundJob(lambda: load_preset_snapshot(registry, previous)))
        self.timer.start()

    def poll(self):
        if self.closed or self.job is None:
            return
        generation, callback, previous, job = self.job
        result = job.poll()
        if result is None:
            return
        self.job = None
        if generation != self.generation:
            self._start()
            return
        if result['ok']:
            try:
                sources = dict((source['id'], source) for source in self.registry.sources())
                snapshot = result['value']
                stale = (snapshot.sources != sources or snapshot.cache_changed or
                         snapshot.cache_tokens != snapshot_cache_tokens(self.registry, sources))
            except Exception as exc:
                result = {'ok': False, 'error': text_type(exc)}
                stale = False
            if stale:
                self.pending = (generation, callback, previous)
                self._start()
                return
        self.busy = False
        self.timer.stop()
        callback(result)

    def cancel(self, *args):
        self.closed = True
        self.generation += 1
        self.timer.stop()
        self.pending = None
        self.job = None
        self.busy = False
