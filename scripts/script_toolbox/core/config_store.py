# -*- coding: utf-8 -*-
from __future__ import print_function

from .config import save_config, file_revision, config_path


class ConfigStore(object):
    """Track the active configuration document and coalesce persistence.

    ConfigStore deliberately does not own a thread or Qt timer. The DCC UI
    schedules debounced flushes on its main thread, while this class owns the
    dirty-state and write contract in a host-independent form.
    """

    def __init__(
        self,
        document=None,
        path=None,
        writer=None
    ):
        self.document = document
        self.path = path
        self.writer = writer or save_config
        self.revision = (getattr(document, "source_revision", file_revision(path or config_path()))
                         if writer is None else None)
        self.dirty = False
        self.write_count = 0

    def replace_document(
        self,
        document,
        dirty=False
    ):
        self.document = document
        if hasattr(document, "source_revision"):
            self.revision = document.source_revision
        self.dirty = bool(
            dirty
        )
        return self.document

    def mark_dirty(
        self,
        document=None
    ):
        if document is not None:
            self.document = document

        self.dirty = True
        return self.document

    def clear_dirty(self):
        self.dirty = False

    def flush(self, force=False):
        if self.document is None:
            raise RuntimeError(
                "ConfigStore has no configuration document to save."
            )

        if (
            not self.dirty and
            not force
        ):
            return None

        # Keep dirty=True until the writer succeeds. A disk/config recovery
        # failure therefore never makes unsaved in-memory changes look clean.
        if self.writer is save_config:
            result, self.revision = self.writer(
                self.document, path=self.path, expected_revision=self.revision,
                return_revision=True)
        else:
            result = self.writer(self.document, path=self.path)
        self.dirty = False
        self.write_count += 1
        return result

    def save(
        self,
        document=None
    ):
        self.mark_dirty(
            document=document
        )
        return self.flush()


__all__ = [
    "ConfigStore",
]
