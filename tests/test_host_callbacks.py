# -*- coding: utf-8 -*-
from __future__ import print_function

from script_toolbox.hosts.base import BaseHost
from script_toolbox.hosts.callbacks import EVENT_SELECTION_CHANGED
from script_toolbox.hosts.callbacks import HostCallbackGroup
from script_toolbox.hosts.callbacks import HostCallbackHandle


class FakeHost(BaseHost):

    def __init__(self):
        self.removed = []
        self.created = []

    def supports_callback(self, event_name):
        return event_name == EVENT_SELECTION_CHANGED

    def _remove(self, native_handle):
        self.removed.append(native_handle)
        return True

    def add_callback(self, event_name, callback):
        if not self.supports_callback(event_name):
            return None

        native_handle = len(self.created) + 1
        self.created.append(
            (native_handle, callback)
        )
        return HostCallbackHandle(
            event_name,
            native_handle,
            self._remove
        )


def test_base_host_reports_no_native_callbacks():
    host = BaseHost()

    assert host.supports_callback(
        EVENT_SELECTION_CHANGED
    ) is False
    assert host.add_callback(
        EVENT_SELECTION_CHANGED,
        lambda: None
    ) is None
    assert host.remove_callback(None) is False


def test_callback_handle_is_idempotent():
    removed = []

    handle = HostCallbackHandle(
        EVENT_SELECTION_CHANGED,
        42,
        lambda native_handle: removed.append(
            native_handle
        ) or True
    )

    assert handle.active is True
    assert handle.close() is True
    assert handle.active is False
    assert handle.close() is False
    assert removed == [42]


def test_callback_group_owns_and_clears_handles():
    host = FakeHost()
    group = HostCallbackGroup(host)
    callback = lambda: None

    assert group.subscribe(
        EVENT_SELECTION_CHANGED,
        callback
    ) is True
    assert len(group) == 1
    assert len(group.handles) == 1

    assert group.clear() == 1
    assert len(group) == 0
    assert host.removed == [1]

    assert group.clear() == 0
    assert host.removed == [1]


def test_callback_group_keeps_polling_fallback_contract():
    host = BaseHost()
    group = HostCallbackGroup(host)

    assert group.subscribe(
        EVENT_SELECTION_CHANGED,
        lambda: None
    ) is False
    assert len(group) == 0
