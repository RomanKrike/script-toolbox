# -*- coding: utf-8 -*-

from script_toolbox.core.state_refresh import StateRefreshQueue


def test_queue_starts_idle():
    queue = StateRefreshQueue()

    assert queue.pending is False


def test_repeated_requests_coalesce_until_consumed():
    queue = StateRefreshQueue()

    assert queue.request() is True
    assert queue.pending is True
    assert queue.request() is False
    assert queue.request() is False

    assert queue.consume() is True
    assert queue.pending is False
    assert queue.consume() is False


def test_new_window_can_be_scheduled_after_consume():
    queue = StateRefreshQueue()

    assert queue.request() is True
    assert queue.consume() is True
    assert queue.request() is True


def test_cancel_clears_pending_request():
    queue = StateRefreshQueue()

    assert queue.cancel() is False
    assert queue.request() is True
    assert queue.cancel() is True
    assert queue.pending is False
    assert queue.request() is True
