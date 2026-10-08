# -*- coding: utf-8 -*-
"""One mutation entry point shared by scripts and runtime controls."""
from __future__ import print_function

from ..compat import QtCore
from ..core.item_changes import Item, resolve_item, update_item


class ItemChangesMixin(object):
    def item(self, key):
        return Item(self, key)

    def change_item(self, key, properties):
        if QtCore.QThread.currentThread() != self.thread():
            raise RuntimeError("Item.set must run on the GUI thread")
        item = resolve_item(self.config, key)
        change = update_item(item, properties)
        if not change.changed:
            return change
        # Saving and user callbacks never participate in candidate validation.
        schedule = getattr(self, "schedule_save", self.save)
        schedule()
        surface = getattr(self, "runtime_surface", None)
        if surface is not None:
            surface.context.apply_item_change(item, change)
        expression_edit = any("expression" in path or path in ("ui.visible", "ui.enabled")
                              for path in change.fields)
        self.refresh_expressions(None if expression_edit else key, recompile=expression_edit)
        if "props.value" in change.fields:
            self.refresh_state_buttons()
            self._dispatch_value_change(item, change)
        return change

    def _dispatch_value_change(self, item, change):
        queue = getattr(self, "_item_change_events", None)
        event = (item, change.before["props.value"], change.after["props.value"])
        if queue is not None:
            queue.append(event)
            return
        queue = self._item_change_events = [event]
        try:
            processed = 0
            while queue:
                processed += 1
                if processed > 100:
                    raise RuntimeError("Cyclic value_changed bindings: exceeded 100 changes")
                self._run_on_change(*queue.pop(0))
        finally:
            self._item_change_events = None
