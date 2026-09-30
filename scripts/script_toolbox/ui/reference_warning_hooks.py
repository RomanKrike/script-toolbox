# -*- coding: utf-8 -*-
from __future__ import print_function

from ..core.references import rewrite_document_references_result
from ..pycompat import text_type


_HOOK_MARKER = "_script_toolbox_reference_warning_hook"
_HOOK_BASE = "_script_toolbox_reference_warning_base"


def _unwrap_base(base_class):
    while getattr(base_class, _HOOK_MARKER, False):
        previous = getattr(base_class, _HOOK_BASE, None)
        if previous is None or previous is base_class:
            break
        base_class = previous
    return base_class


class ReferenceWarningEditorMixin(object):

    def __init__(self, *args, **kwargs):
        self._pending_reference_warning = []
        super(ReferenceWarningEditorMixin, self).__init__(*args, **kwargs)

    def _reference_warning(self, unresolved_items):
        unresolved_items = list(unresolved_items or [])
        if not unresolved_items:
            return

        names = []
        for entry in unresolved_items:
            label = text_type(
                entry.get("label") or
                entry.get("name") or
                entry.get("id") or
                "script"
            )
            if label not in names:
                names.append(label)

        preview = ", ".join(names[:5])
        if len(names) > 5:
            preview += " (+{0})".format(len(names) - 5)

        message = (
            "Some script references could not be updated automatically. "
            "Review the affected scripts."
        )
        if preview:
            message += " Affected: {0}.".format(preview)
        self.status.setText(message)

    def _clone_data(self, data, used_names=None):
        clone, result = self.document_controller.clone_subtree_result(
            data,
            used_names
        )
        unresolved = result.get("unresolved_items", [])
        if unresolved:
            self._pending_reference_warning.extend(unresolved)
        return clone

    def _linked_rename_command(
        self,
        item_id,
        before,
        old_name,
        new_name
    ):
        command, changed_ids = super(ReferenceWarningEditorMixin, self)._linked_rename_command(item_id,
            before,
            old_name,
            new_name
        )

        # Supported direct literals were already rewritten by the base
        # operation. A second structured pass therefore reports only the
        # old-name references that remain unsafe to rewrite automatically.
        result = rewrite_document_references_result(
            self.document_controller.document,
            {old_name: new_name}
        )
        self._reference_warning(
            result.get("unresolved_items", [])
        )
        return command, changed_ids

    def duplicate_selected(self, target_item=None):
        result = super(ReferenceWarningEditorMixin, self).duplicate_selected(target_item
        )
        pending = self._pending_reference_warning
        self._pending_reference_warning = []
        self._reference_warning(pending)
        return result


def build_reference_warning_editor_class(base_class):
    base_class = _unwrap_base(base_class)
    return type("InterfaceEditor", (ReferenceWarningEditorMixin, base_class), {
        _HOOK_MARKER: True, _HOOK_BASE: base_class,
    })


__all__ = [
    "ReferenceWarningEditorMixin",
    "build_reference_warning_editor_class",
]
