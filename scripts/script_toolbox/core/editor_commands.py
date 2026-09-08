# -*- coding: utf-8 -*-
from __future__ import print_function

import copy

from ..pycompat import text_type


class EditorCommand(object):
    """Base reversible command for the staged editor document."""

    def __init__(
        self,
        label="Edit",
        selection_before=None,
        selection_after=None
    ):
        self.label = text_type(label or "Edit")
        self.selection_before = selection_before
        self.selection_after = selection_after

    def undo(self, controller):
        raise NotImplementedError

    def redo(self, controller):
        raise NotImplementedError


class ItemStateCommand(EditorCommand):
    """Change non-structural state for one item."""

    def __init__(
        self,
        item_id,
        before,
        after,
        label="Edit Parameter",
        selection_before=None,
        selection_after=None
    ):
        EditorCommand.__init__(
            self,
            label=label,
            selection_before=selection_before,
            selection_after=selection_after
        )
        self.item_id = text_type(item_id)
        self.before = copy.deepcopy(before)
        self.after = copy.deepcopy(after)

    def undo(self, controller):
        controller.apply_item_state(
            self.item_id,
            self.before
        )

    def redo(self, controller):
        controller.apply_item_state(
            self.item_id,
            self.after
        )


class DocumentDeltaCommand(EditorCommand):
    """
    Reversible document delta.

    Unchanged item payloads are never copied into the command. Structural
    edits store ID-only topology plus payloads for subtrees that disappear
    from one side of the command. Common changed items store only their
    non-structural state.
    """

    def __init__(
        self,
        before_topology,
        after_topology,
        before_missing,
        after_missing,
        before_states,
        after_states,
        before_root,
        after_root,
        label="Edit Interface",
        selection_before=None,
        selection_after=None
    ):
        EditorCommand.__init__(
            self,
            label=label,
            selection_before=selection_before,
            selection_after=selection_after
        )
        self.before_topology = copy.deepcopy(before_topology)
        self.after_topology = copy.deepcopy(after_topology)
        self.before_missing = copy.deepcopy(before_missing)
        self.after_missing = copy.deepcopy(after_missing)
        self.before_states = copy.deepcopy(before_states)
        self.after_states = copy.deepcopy(after_states)
        self.before_root = copy.deepcopy(before_root)
        self.after_root = copy.deepcopy(after_root)

    def _apply(
        self,
        controller,
        topology,
        missing,
        states,
        root_state
    ):
        controller.apply_topology(
            topology,
            payloads=missing
        )
        controller.apply_root_state(
            root_state
        )
        for item_id, state in states.items():
            controller.apply_item_state(
                item_id,
                state,
                rebuild=False
            )
        controller.rebuild_index()

    def undo(self, controller):
        self._apply(
            controller,
            self.before_topology,
            self.before_missing,
            self.before_states,
            self.before_root
        )

    def redo(self, controller):
        self._apply(
            controller,
            self.after_topology,
            self.after_missing,
            self.after_states,
            self.after_root
        )


class CommandHistory(object):
    """Bounded command stack with standard redo invalidation semantics."""

    def __init__(self, controller, limit=100):
        self.controller = controller
        self.limit = max(1, int(limit))
        self.undo_stack = []
        self.redo_stack = []

    @property
    def can_undo(self):
        return bool(self.undo_stack)

    @property
    def can_redo(self):
        return bool(self.redo_stack)

    def clear(self):
        del self.undo_stack[:]
        del self.redo_stack[:]

    def push_applied(self, command):
        if command is None:
            return False

        self.undo_stack.append(command)
        if len(self.undo_stack) > self.limit:
            del self.undo_stack[:-self.limit]
        del self.redo_stack[:]
        return True

    def undo(self):
        if not self.undo_stack:
            return None

        command = self.undo_stack.pop()
        command.undo(self.controller)
        self.redo_stack.append(command)
        return command

    def redo(self):
        if not self.redo_stack:
            return None

        command = self.redo_stack.pop()
        command.redo(self.controller)
        self.undo_stack.append(command)
        return command


def _topology_ids(topology):
    result = set(
        text_type(item_id)
        for item_id in topology.get("roots", [])
    )
    for parent_id, child_ids in topology.get("children", {}).items():
        result.add(text_type(parent_id))
        result.update(
            text_type(item_id)
            for item_id in child_ids
        )
    return result


def _reachable_refs(controller, topology):
    refs = {}
    for item_id in _topology_ids(topology):
        item = controller.item_cache.get(item_id)
        if item is not None:
            refs[item_id] = item
    return refs


class DocumentCapture(object):
    """Lightweight pre-change capture used to build a semantic delta."""

    def __init__(self, controller):
        self.topology = controller.capture_topology()
        self.root_state = controller.root_state()
        self.item_refs = _reachable_refs(
            controller,
            self.topology
        )
        self.item_states = {}

        for item_id, item in self.item_refs.items():
            self.item_states[item_id] = controller.item_state(item)


def _parent_map(topology):
    parents = {}

    for item_id in topology.get("roots", []):
        parents[text_type(item_id)] = None

    for parent_id, children in topology.get("children", {}).items():
        for item_id in children:
            parents[text_type(item_id)] = text_type(parent_id)

    return parents


def _delta_roots(item_ids, topology):
    item_ids = set(text_type(value) for value in item_ids)
    parents = _parent_map(topology)
    roots = []

    for item_id in item_ids:
        parent_id = parents.get(item_id)
        if parent_id not in item_ids:
            roots.append(item_id)

    return roots


def _subtree_from_refs(item_id, refs):
    item = refs.get(text_type(item_id))
    if item is None:
        return None
    return copy.deepcopy(item)


def build_document_delta(
    controller,
    capture,
    label="Edit Interface",
    selection_before=None,
    selection_after=None
):
    """Build a command containing only changed document state."""
    after_topology = controller.capture_topology()
    after_root = controller.root_state()
    after_refs = _reachable_refs(
        controller,
        after_topology
    )
    after_states = {}

    for item_id, item in after_refs.items():
        after_states[item_id] = controller.item_state(item)

    before_ids = set(capture.item_refs.keys())
    after_ids = set(after_refs.keys())
    removed_ids = before_ids - after_ids
    added_ids = after_ids - before_ids

    before_missing = {}
    for item_id in _delta_roots(
        removed_ids,
        capture.topology
    ):
        payload = _subtree_from_refs(
            item_id,
            capture.item_refs
        )
        if payload is not None:
            before_missing[item_id] = payload

    after_missing = {}
    for item_id in _delta_roots(
        added_ids,
        after_topology
    ):
        payload = _subtree_from_refs(
            item_id,
            after_refs
        )
        if payload is not None:
            after_missing[item_id] = payload

    changed_before = {}
    changed_after = {}
    for item_id in before_ids.intersection(after_ids):
        before_state = capture.item_states.get(item_id, {})
        after_state = after_states.get(item_id, {})
        if before_state != after_state:
            changed_before[item_id] = before_state
            changed_after[item_id] = after_state

    if (
        capture.topology == after_topology and
        capture.root_state == after_root and
        not before_missing and
        not after_missing and
        not changed_before
    ):
        return None

    return DocumentDeltaCommand(
        capture.topology,
        after_topology,
        before_missing,
        after_missing,
        changed_before,
        changed_after,
        capture.root_state,
        after_root,
        label=label,
        selection_before=selection_before,
        selection_after=selection_after
    )


__all__ = [
    "CommandHistory",
    "DocumentCapture",
    "DocumentDeltaCommand",
    "EditorCommand",
    "ItemStateCommand",
    "build_document_delta",
]
