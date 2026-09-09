# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore
from ..compat import QtGui
from ..core.editor_commands import CommandHistory
from ..core.editor_commands import DocumentCapture
from ..core.editor_commands import ItemStateCommand
from ..core.editor_commands import ItemsStateCommand
from ..core.editor_commands import build_document_delta
from ..core.editor_document import EditorDocumentController
from ..model import normalize_document
from ..pycompat import text_type
from .editor_search import apply_editor_presentation
from .editor_search import filter_existing_parameters as filter_editor_structure
from .editor_search import reapply_existing_filter
from .share_hooks import install_share_controller


_ADAPTER_MARKER = "_script_toolbox_document_controller_adapter"
_LEGACY_BASE = "_script_toolbox_legacy_interface_editor"
_VIEW_ROLE_ID = QtCore.Qt.UserRole + 1


def capture_editor_view_state(editor):
    """Capture selection, expansion and scroll state before an Apply rebuild."""
    expanded = {}

    def visit(tree_item):
        item_id = editor.item_data(
            tree_item,
            _VIEW_ROLE_ID
        )
        if item_id:
            expanded[text_type(item_id)] = bool(
                tree_item.isExpanded()
            )

        for index in range(
            tree_item.childCount()
        ):
            visit(
                tree_item.child(index)
            )

    for index in range(
        editor.tree.topLevelItemCount()
    ):
        visit(
            editor.tree.topLevelItem(index)
        )

    current = editor.tree.currentItem()
    current_id = (
        editor.item_data(
            current,
            _VIEW_ROLE_ID
        )
        if current is not None
        else editor.current_item_id
    )

    state = {
        "current_id": text_type(current_id or ""),
        "expanded": expanded,
        "tree_vertical_scroll": 0,
        "tree_horizontal_scroll": 0,
        "property_vertical_scroll": 0,
    }

    try:
        state["tree_vertical_scroll"] = int(
            editor.tree.verticalScrollBar().value()
        )
        state["tree_horizontal_scroll"] = int(
            editor.tree.horizontalScrollBar().value()
        )
    except Exception:
        pass

    try:
        state["property_vertical_scroll"] = int(
            editor.property_scroll.verticalScrollBar().value()
        )
    except Exception:
        pass

    return state


def restore_editor_view_state(editor, state):
    """Restore an Interface Editor view state after its tree is rebuilt."""
    if not state:
        return

    expanded = state.get(
        "expanded",
        {}
    )

    def visit(tree_item):
        item_id = editor.item_data(
            tree_item,
            _VIEW_ROLE_ID
        )
        item_id = text_type(
            item_id or ""
        )
        if item_id in expanded:
            tree_item.setExpanded(
                bool(expanded[item_id])
            )

        for index in range(
            tree_item.childCount()
        ):
            visit(
                tree_item.child(index)
            )

    for index in range(
        editor.tree.topLevelItemCount()
    ):
        visit(
            editor.tree.topLevelItem(index)
        )

    current_id = text_type(
        state.get("current_id", "") or ""
    )
    if current_id:
        selected = editor.tree_item_by_id(
            current_id
        )
        if selected is not None:
            editor.tree.setCurrentItem(
                selected
            )

    try:
        editor.tree.verticalScrollBar().setValue(
            int(state.get("tree_vertical_scroll", 0))
        )
        editor.tree.horizontalScrollBar().setValue(
            int(state.get("tree_horizontal_scroll", 0))
        )
    except Exception:
        pass

    try:
        editor.property_scroll.verticalScrollBar().setValue(
            int(state.get("property_vertical_scroll", 0))
        )
    except Exception:
        pass


def _unwrap_base(base_class):
    while getattr(base_class, _ADAPTER_MARKER, False):
        legacy = getattr(base_class, _LEGACY_BASE, None)
        if legacy is None or legacy is base_class:
            break
        base_class = legacy
    return base_class


def build_interface_editor_class(base_class):
    """Build a controller-backed adapter around the current legacy class."""
    base_class = _unwrap_base(base_class)

    class InterfaceEditor(base_class):
        """Compatibility adapter moving editor state/history into core."""

        def __init__(self, toolbox, parent=None):
            self.document_controller = EditorDocumentController(
                toolbox.config
            )
            self._command_ready = False
            self._pending_property_id = None
            self._pending_property_before = None
            self._pending_document_capture = None
            self._pending_document_selection = None
            self._next_tree_label = None

            # Share must exist before the legacy constructor calls build_ui(),
            # where _icon_button() resolves dynamically on this instance.
            install_share_controller(self)

            base_class.__init__(
                self,
                toolbox,
                parent=parent
            )

            self.command_history = CommandHistory(
                self.document_controller,
                limit=100
            )
            # Preserve legacy UI checks such as bool(self.undo_stack) while
            # changing the stack contents from documents to commands.
            self.undo_stack = self.command_history.undo_stack
            self.redo_stack = self.command_history.redo_stack
            self._command_ready = True
            self._sync_property_baseline()

            try:
                del self._history_current
            except Exception:
                pass

        # --------------------------------------------------------------
        # Direct UI feature composition
        # --------------------------------------------------------------

        def build_ui(self):
            base_class.build_ui(
                self
            )
            apply_editor_presentation(self)

        def _icon_button(
            self,
            icon_name,
            tooltip,
            callback
        ):
            return self.share_controller.icon_button(
                icon_name,
                tooltip,
                callback
            )

        def show_tree_context_menu(self, point):
            return self.share_controller.show_tree_context_menu(
                point
            )

        def share_settings(self):
            return self.share_controller.share_settings()

        def paste_shared_settings(self):
            return self.share_controller.paste_shared_settings()

        def share_selected(self, target_item=None):
            return self.share_controller.share_selected(
                target_item
            )

        def paste_shared_selected(self):
            return self.share_controller.paste_shared_selected()

        def filter_existing_parameters(self, value):
            return filter_editor_structure(
                self,
                value
            )

        def populate_tree(self):
            base_class.populate_tree(
                self
            )
            reapply_existing_filter(self)

        # --------------------------------------------------------------
        # Document ownership compatibility
        # --------------------------------------------------------------

        @property
        def working(self):
            return self.document_controller.document

        @working.setter
        def working(self, document):
            # Legacy InterfaceEditor callers already copy/normalize external
            # documents before assignment. Internal tree synchronization
            # assembles current item dicts directly, so adopt preserves them.
            self.document_controller.adopt(document)

        @property
        def item_cache(self):
            return self.document_controller.item_cache

        @item_cache.setter
        def item_cache(self, mapping):
            self.document_controller.replace_index(mapping)

        def rebuild_cache(self):
            self.document_controller.rebuild_index()

        def _used_names(self):
            return self.document_controller.used_names()

        def _unique_name(self, base, used_names):
            return self.document_controller.unique_name(
                base,
                used_names
            )

        def _clone_data(self, data, used_names=None):
            return self.document_controller.clone_subtree(
                data,
                used_names
            )

        def _cache_subtree(self, data):
            self.document_controller.cache_subtree(data)

        def validate_internal_names(self):
            duplicate = self.document_controller.duplicate_name()

            if duplicate is None:
                return True

            QtGui.QMessageBox.warning(
                self,
                "Duplicate Name",
                "Name '{0}' is used more than once.".format(
                    duplicate
                )
            )
            return False

        # --------------------------------------------------------------
        # Command history
        # --------------------------------------------------------------

        def _sync_property_baseline(self):
            if not getattr(self, "_command_ready", False):
                return

            item_id = self.current_item_id
            item = (
                self.document_controller.find_by_id(item_id)
                if item_id
                else None
            )

            if item is None:
                self._pending_property_id = None
                self._pending_property_before = None
                return

            self._pending_property_id = text_type(item_id)
            self._pending_property_before = (
                self.document_controller.item_state(item)
            )

        def _linked_rename_command(
            self,
            item_id,
            before,
            old_name,
            new_name
        ):
            """Apply a name remap and capture only items changed by the link."""
            states_before = {}
            for candidate_id, candidate in self.document_controller.item_cache.items():
                states_before[candidate_id] = (
                    self.document_controller.item_state(candidate)
                )

            # The selected item has already been edited by the property widget.
            # Restore its true pre-edit state in the command's before side.
            states_before[item_id] = before

            changed_reference_ids = (
                self.document_controller.rename_item_references(
                    item_id,
                    old_name,
                    new_name
                )
            )

            changed_before = {}
            changed_after = {}
            for candidate_id, before_state in states_before.items():
                candidate = self.document_controller.find_by_id(
                    candidate_id
                )
                if candidate is None:
                    continue

                after_state = self.document_controller.item_state(
                    candidate
                )
                if before_state == after_state:
                    continue

                changed_before[candidate_id] = before_state
                changed_after[candidate_id] = after_state

            if not changed_before:
                return None, changed_reference_ids

            return (
                ItemsStateCommand(
                    changed_before,
                    changed_after,
                    label="Rename Parameter",
                    selection_before=item_id,
                    selection_after=item_id
                ),
                changed_reference_ids
            )

        def schedule_history(self):
            if self._history_restoring:
                return
            self.history_timer.start()

        def commit_history(self, sync_tree=True):
            if (
                not getattr(self, "_command_ready", False) or
                self._history_restoring
            ):
                return

            if self.history_timer.isActive():
                self.history_timer.stop()

            if self._pending_document_capture is not None:
                capture = self._pending_document_capture
                selection_before = self._pending_document_selection
                self._pending_document_capture = None
                self._pending_document_selection = None

                command = build_document_delta(
                    self.document_controller,
                    capture,
                    label="Import Toolbox",
                    selection_before=selection_before,
                    selection_after=self.current_item_id
                )
                self.command_history.push_applied(command)
                self._sync_property_baseline()
                return

            item_id = self._pending_property_id
            before = self._pending_property_before
            if not item_id or before is None:
                self._sync_property_baseline()
                return

            if sync_tree and self.current_property_editor is not None:
                try:
                    self.current_property_editor.write_to_item()
                except Exception:
                    pass

            item = self.document_controller.find_by_id(item_id)
            if item is None:
                self._sync_property_baseline()
                return

            after = self.document_controller.item_state(item)
            if before != after:
                old_name = text_type(before.get("name", ""))
                new_name = text_type(after.get("name", ""))
                changed_reference_ids = set()

                if old_name and new_name and old_name != new_name:
                    command, changed_reference_ids = (
                        self._linked_rename_command(
                            item_id,
                            before,
                            old_name,
                            new_name
                        )
                    )
                else:
                    command = ItemStateCommand(
                        item_id,
                        before,
                        after,
                        label="Edit Parameter",
                        selection_before=item_id,
                        selection_after=item_id
                    )

                self.command_history.push_applied(command)

                # A self-reference can change the selected item's script text.
                # Rebind so the visible editor cannot later write stale text
                # back over the remapped payload.
                if (
                    item_id in changed_reference_ids and
                    self.current_property_editor is not None
                ):
                    try:
                        self.current_property_editor.bind(item)
                    except Exception:
                        pass

            self._pending_property_before = (
                self.document_controller.item_state(item)
            )

        def _restore_command_ui(self, command, is_undo):
            target_id = (
                command.selection_before
                if is_undo
                else command.selection_after
            )
            self._history_restoring = True
            try:
                self.populate_tree()

                if target_id:
                    tree_item = self.tree_item_by_id(
                        text_type(target_id)
                    )
                    if tree_item is not None:
                        self.tree.setCurrentItem(tree_item)

                action = "Undo" if is_undo else "Redo"
                self.status.setText(
                    "{0}: {1} — Apply or Accept to save.".format(
                        action,
                        command.label
                    )
                )
            finally:
                self._history_restoring = False
                self._sync_property_baseline()

        def undo(self):
            if self.history_timer.isActive():
                self.commit_history()

            command = self.command_history.undo()
            if command is None:
                return
            self._restore_command_ui(
                command,
                True
            )

        def redo(self):
            if self.history_timer.isActive():
                self.commit_history()

            command = self.command_history.redo()
            if command is None:
                return
            self._restore_command_ui(
                command,
                False
            )

        def selection_changed(self, current, previous):
            if (
                getattr(self, "_command_ready", False) and
                not self._history_restoring and
                self.history_timer.isActive()
            ):
                self.commit_history(sync_tree=False)

            result = base_class.selection_changed(
                self,
                current,
                previous
            )
            self._sync_property_baseline()
            return result

        def property_changed(self):
            return base_class.property_changed(self)

        def tree_changed(self):
            if self._history_restoring:
                return

            if self.history_timer.isActive():
                self.commit_history(sync_tree=False)

            capture = DocumentCapture(
                self.document_controller
            )
            selection_before = self.current_item_id
            label = self._next_tree_label or "Move/Reorder Parameter"
            self._next_tree_label = None

            self.sync_working_from_tree()
            self.status.setText(
                "Modified — Apply or Accept to save."
            )

            command = build_document_delta(
                self.document_controller,
                capture,
                label=label,
                selection_before=selection_before,
                selection_after=self.current_item_id
            )
            self.command_history.push_applied(command)
            self._sync_property_baseline()

        def _call_tree_action(self, label, callback, *args, **kwargs):
            previous = self._next_tree_label
            self._next_tree_label = label
            try:
                return callback(
                    self,
                    *args,
                    **kwargs
                )
            finally:
                # tree_changed consumes the label on successful mutation.
                if self._next_tree_label == label:
                    self._next_tree_label = previous

        def create_from_palette(self, palette_item, column=0):
            return self._call_tree_action(
                "Create Parameter",
                base_class.create_from_palette,
                palette_item,
                column
            )

        def paste_selected(self):
            return self._call_tree_action(
                "Paste Parameter",
                base_class.paste_selected
            )

        def duplicate_selected(self, target_item=None):
            return self._call_tree_action(
                "Duplicate Parameter",
                base_class.duplicate_selected,
                target_item
            )

        def move_selected(self, direction):
            return self._call_tree_action(
                "Move Parameter",
                base_class.move_selected,
                direction
            )

        def delete_selected(self):
            return self._call_tree_action(
                "Delete Parameter",
                base_class.delete_selected
            )

        def import_settings(self):
            if self.history_timer.isActive():
                self.commit_history(sync_tree=False)

            self.sync_working_from_tree()
            capture = DocumentCapture(
                self.document_controller
            )
            self._pending_document_capture = capture
            self._pending_document_selection = self.current_item_id

            try:
                return base_class.import_settings(self)
            finally:
                # Cancel/error paths do not call commit_history().
                self._pending_document_capture = None
                self._pending_document_selection = None
                self._sync_property_baseline()

        # --------------------------------------------------------------
        # Apply view-state preservation
        # --------------------------------------------------------------

        def _capture_tree_view_state(self):
            return capture_editor_view_state(
                self
            )

        def _restore_tree_view_state(self, state):
            restore_editor_view_state(
                self,
                state
            )

        def apply_changes(self):
            view_state = self._capture_tree_view_state()

            if self.history_timer.isActive():
                self.commit_history()

            self.fix_tree_structure()
            self.sync_working_from_tree()

            if not self.validate_internal_names():
                return False

            self.toolbox.config = normalize_document(
                self.document_controller.snapshot()
            )
            self.toolbox.save()
            self.toolbox.rebuild()

            # Re-seed the staged controller from the applied runtime config
            # without creating a history snapshot. Existing command objects
            # remain valid because item IDs are stable across Apply.
            self.document_controller.replace(
                self.toolbox.config
            )
            self.populate_tree()
            self.status.setText(
                "Applied."
            )
            self._restore_tree_view_state(
                view_state
            )
            self._sync_property_baseline()
            return True

    setattr(
        InterfaceEditor,
        _ADAPTER_MARKER,
        True
    )
    setattr(
        InterfaceEditor,
        _LEGACY_BASE,
        base_class
    )
    InterfaceEditor.__name__ = "InterfaceEditor"
    return InterfaceEditor


__all__ = [
    "build_interface_editor_class",
    "capture_editor_view_state",
    "restore_editor_view_state",
]
