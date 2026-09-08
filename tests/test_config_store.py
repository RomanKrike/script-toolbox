# -*- coding: utf-8 -*-

import pytest

from script_toolbox.core.config_store import ConfigStore


def test_store_starts_clean_and_skips_clean_flush():
    calls = []

    def writer(document, path=None):
        calls.append((document, path))
        return path

    document = {"sections": []}
    store = ConfigStore(
        document=document,
        path="toolbox.json",
        writer=writer
    )

    assert store.dirty is False
    assert store.flush() is None
    assert calls == []
    assert store.write_count == 0


def test_many_dirty_marks_coalesce_into_one_flush():
    calls = []

    def writer(document, path=None):
        calls.append((document, path))
        return path

    document = {"sections": []}
    store = ConfigStore(
        document=document,
        path="toolbox.json",
        writer=writer
    )

    for _ in range(20):
        store.mark_dirty()

    assert store.dirty is True

    assert store.flush() == "toolbox.json"
    assert len(calls) == 1
    assert calls[0][0] is document
    assert calls[0][1] == "toolbox.json"
    assert store.dirty is False
    assert store.write_count == 1

    assert store.flush() is None
    assert len(calls) == 1


def test_mark_dirty_can_rebind_document_before_flush():
    written = []

    def writer(document, path=None):
        written.append(document)
        return path

    first = {"name": "first"}
    second = {"name": "second"}
    store = ConfigStore(
        document=first,
        writer=writer
    )

    store.mark_dirty(
        second
    )
    store.flush()

    assert written == [second]
    assert store.document is second


def test_replace_document_can_reset_dirty_state():
    store = ConfigStore(
        document={"name": "first"},
        writer=lambda document, path=None: path
    )

    store.mark_dirty()
    assert store.dirty is True

    replacement = {"name": "replacement"}
    store.replace_document(
        replacement,
        dirty=False
    )

    assert store.document is replacement
    assert store.dirty is False


def test_explicit_save_marks_and_flushes_immediately():
    calls = []

    def writer(document, path=None):
        calls.append(document)
        return "saved"

    document = {"sections": []}
    store = ConfigStore(
        document=document,
        writer=writer
    )

    assert store.save() == "saved"
    assert calls == [document]
    assert store.dirty is False
    assert store.write_count == 1


def test_failed_flush_keeps_store_dirty_for_retry():
    attempts = []

    def writer(document, path=None):
        attempts.append(document)
        raise IOError("disk full")

    document = {"sections": []}
    store = ConfigStore(
        document=document,
        writer=writer
    )
    store.mark_dirty()

    with pytest.raises(IOError):
        store.flush()

    assert attempts == [document]
    assert store.dirty is True
    assert store.write_count == 0


def test_force_flush_writes_clean_document():
    calls = []

    def writer(document, path=None):
        calls.append(document)
        return "forced"

    document = {"sections": []}
    store = ConfigStore(
        document=document,
        writer=writer
    )

    assert store.flush(force=True) == "forced"
    assert calls == [document]
    assert store.dirty is False
    assert store.write_count == 1


def test_flush_requires_document():
    store = ConfigStore(
        writer=lambda document, path=None: path
    )
    store.mark_dirty()

    with pytest.raises(RuntimeError):
        store.flush()
