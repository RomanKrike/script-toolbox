# -*- coding: utf-8 -*-
from __future__ import print_function

import copy

from ..compat import QtCore
from ..compat import QtGui
from ..core.editor_commands import DocumentCapture
from ..core.editor_commands import build_document_delta
from ..model import create_item
from ..model import normalize_document
from ..pycompat import text_type
from ..share import ShareError
from ..share import extract_share_code
from ..share import fetch_shared_data
from ..share import looks_like_share_code
from ..share import share_data
from ..style import metrics
from .icon_button import ICON_BUTTON_COMPACT
from .icon_button import create_icon_button
from .layout_helpers import configure_layout


class _ShareWorker(QtCore.QThread):
    completed = QtCore.Signal(object)

    def __init__(self, operation, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.operation = operation

    def run(self):
        try:
            result = {
                "ok": True,
                "value": self.operation(),
            }
        except Exception as exc:
            result = {
                "ok": False,
                "error": text_type(exc),
            }
        self.completed.emit(result)


def _clipboard_text():
    try:
        return text_type(
            QtGui.QApplication.clipboard().text() or ""
        )
    except Exception:
        return ""


def _set_clipboard_text(value):
    QtGui.QApplication.clipboard().setText(
        text_type(value)
    )


class ShareController(object):
    """Compose share UI and operations into an Interface Editor instance."""

    def __init__(self, editor):
        self.editor = editor
        self._share_workers = []
        self._share_callbacks = {}

        # Preserve stable public references used by editor integrations and
        # compatibility callers while keeping their ownership explicit.
        editor._share_workers = self._share_workers
        editor._share_callbacks = self._share_callbacks
        editor.import_button = None
        editor.export_button = None
        editor.share_paste_button = None
        editor.share_button = None
        editor.share_action_widget = None
        editor.share_action_layout = None

    # ------------------------------------------------------------------
    # UI integration
    # ------------------------------------------------------------------

    def icon_button(
        self,
        icon_name,
        tooltip,
        callback
    ):
        editor = self.editor

        if icon_name == "export":
            return self._build_share_action_cluster(
                tooltip,
                callback
            )

        button = create_icon_button(
            icon_name,
            tooltip,
            callback,
            parent=editor,
            preset=ICON_BUTTON_COMPACT
        )

        if icon_name == "import":
            editor.import_button = button

        return button

    def _build_share_action_cluster(
        self,
        export_tooltip,
        export_callback
    ):
        editor = self.editor
        cluster = QtGui.QWidget(editor)
        cluster.setObjectName("ShareActionCluster")
        layout = QtGui.QHBoxLayout(cluster)
        configure_layout(
            layout,
            margins=metrics.MARGINS_NONE,
            spacing=metrics.SHARE_ACTION_SPACING
        )

        editor.export_button = create_icon_button(
            "export",
            export_tooltip,
            export_callback,
            parent=cluster,
            preset=ICON_BUTTON_COMPACT
        )
        editor.share_paste_button = create_icon_button(
            "cloud-download",
            "Paste Shared Toolbox from Clipboard",
            self.paste_shared_settings,
            parent=cluster,
            preset=ICON_BUTTON_COMPACT
        )
        editor.share_button = create_icon_button(
            "cloud-upload",
            "Share Toolbox and Copy STB1 Code",
            self.share_settings,
            parent=cluster,
            preset=ICON_BUTTON_COMPACT
        )

        layout.addWidget(editor.export_button)
        layout.addWidget(editor.share_paste_button)
        layout.addWidget(editor.share_button)

        editor.share_action_widget = cluster
        editor.share_action_layout = layout
        return cluster

    def show_tree_context_menu(self, point):
        editor = self.editor
        item = editor.tree.itemAt(point)
        if item is not None:
            editor.tree.setCurrentItem(item)

        menu = QtGui.QMenu(editor.tree)
        undo_action = menu.addAction("Undo")
        redo_action = menu.addAction("Redo")
        undo_action.setEnabled(bool(editor.undo_stack))
        redo_action.setEnabled(bool(editor.redo_stack))
        menu.addSeparator()

        copy_action = menu.addAction("Copy")
        paste_action = menu.addAction("Paste")
        duplicate_action = menu.addAction("Duplicate")
        paste_action.setEnabled(
            editor.clipboard_item is not None
        )

        menu.addSeparator()
        share_action = menu.addAction("Share")
        paste_shared_action = menu.addAction("Paste Shared")
        share_action.setEnabled(item is not None)
        paste_shared_action.setEnabled(
            looks_like_share_code(
                _clipboard_text()
            )
        )

        menu.addSeparator()
        delete_action = menu.addAction("Delete")

        action = menu.exec_(
            editor.tree.viewport().mapToGlobal(point)
        )

        if action == undo_action:
            editor.undo()
        elif action == redo_action:
            editor.redo()
        elif action == copy_action:
            editor.copy_selected()
        elif action == paste_action:
            editor.paste_selected()
        elif action == duplicate_action:
            editor.duplicate_selected(item)
        elif action == share_action:
            self.share_selected(item)
        elif action == paste_shared_action:
            self.paste_shared_selected()
        elif action == delete_action:
            editor.delete_selected()

    # ------------------------------------------------------------------
    # Worker helpers
    # ------------------------------------------------------------------

    def _start_share_operation(
        self,
        status_text,
        operation,
        callback
    ):
        editor = self.editor
        worker = _ShareWorker(
            operation,
            editor
        )
        self._share_workers.append(worker)
        self._share_callbacks[worker] = callback
        worker.completed.connect(
            lambda result, current=worker: self._share_operation_finished(
                current,
                result
            )
        )
        editor.status.setText(status_text)
        worker.start()

    def _share_operation_finished(
        self,
        worker,
        result
    ):
        editor = self.editor
        callback = self._share_callbacks.pop(
            worker,
            None
        )
        try:
            self._share_workers.remove(worker)
        except ValueError:
            pass

        try:
            worker.deleteLater()
        except Exception:
            pass

        if not result.get("ok"):
            editor.status.setText("Share operation failed.")
            QtGui.QMessageBox.critical(
                editor,
                "Script Toolbox Share",
                result.get(
                    "error",
                    "Unknown share error."
                )
            )
            return

        if callback is not None:
            callback(
                result.get("value")
            )

    def _clipboard_share_code(self):
        editor = self.editor
        try:
            return extract_share_code(
                _clipboard_text()
            )
        except ShareError as exc:
            QtGui.QMessageBox.warning(
                editor,
                "Script Toolbox Share",
                text_type(exc)
            )
            return None

    def _share_code_ready(self, code, label):
        editor = self.editor
        _set_clipboard_text(code)
        editor.status.setText(
            "{0} shared. STB1 code copied to clipboard.".format(
                label
            )
        )

    # ------------------------------------------------------------------
    # Whole toolbox share / paste
    # ------------------------------------------------------------------

    def share_settings(self):
        editor = self.editor
        editor.sync_working_from_tree()

        if not editor.validate_internal_names():
            return

        document = copy.deepcopy(
            editor.working
        )
        self._start_share_operation(
            "Encrypting and sharing toolbox...",
            lambda: share_data(
                "config",
                document
            ),
            lambda code: self._share_code_ready(
                code,
                "Toolbox"
            )
        )

    def paste_shared_settings(self):
        code = self._clipboard_share_code()
        if not code:
            return

        self._start_share_operation(
            "Downloading and decrypting shared toolbox...",
            lambda: fetch_shared_data(code),
            self._shared_settings_ready
        )

    def _shared_settings_ready(self, payload):
        editor = self.editor
        if payload.get("type") != "config":
            QtGui.QMessageBox.warning(
                editor,
                "Script Toolbox Share",
                "This STB1 code contains a parameter, not a full toolbox. "
                "Use Paste Shared from the parameter context menu."
            )
            editor.status.setText(
                "Shared data was not a full toolbox."
            )
            return

        imported = normalize_document(
            copy.deepcopy(
                payload.get("data")
            )
        )

        modes = [
            "Replace Toolbox",
            "Append to Toolbox",
            "Insert into Selected Folder",
        ]
        choice = QtGui.QInputDialog.getItem(
            editor,
            "Paste Shared Toolbox",
            "Paste mode:",
            modes,
            0,
            False
        )

        if isinstance(choice, (tuple, list)):
            if len(choice) < 2 or not choice[1]:
                editor.status.setText(
                    "Shared toolbox paste cancelled."
                )
                return
            mode = text_type(choice[0])
        else:
            mode = text_type(choice)

        if not mode:
            return

        editor.sync_working_from_tree()
        capture = DocumentCapture(
            editor.document_controller
        )
        selection_before = editor.current_item_id
        current_id = editor.current_item_id

        if mode == "Replace Toolbox":
            editor.working = normalize_document(
                copy.deepcopy(imported)
            )
            current_id = None

        elif mode == "Append to Toolbox":
            used_names = editor._used_names()
            for section in imported.get("sections", []):
                editor.working.setdefault(
                    "sections",
                    []
                ).append(
                    editor._clone_data(
                        section,
                        used_names
                    )
                )

        else:
            current = editor.tree.currentItem()
            target_tree = editor.nearest_folder(current)

            if target_tree is None:
                target_tree = editor.ensure_root_folder()

            target_id = editor.item_data(
                target_tree,
                editor.ROLE_ID
            ) if hasattr(editor, "ROLE_ID") else editor.item_data(
                target_tree,
                QtCore.Qt.UserRole + 1
            )
            target = editor.item_cache.get(target_id)

            if target is None:
                QtGui.QMessageBox.warning(
                    editor,
                    "Script Toolbox Share",
                    "Select a Folder before using Insert mode."
                )
                return

            used_names = editor._used_names()
            target.setdefault("items", [])
            for section in imported.get("sections", []):
                target["items"].append(
                    editor._clone_data(
                        section,
                        used_names
                    )
                )
            current_id = target_id

        editor.populate_tree()
        if current_id:
            selected = editor.tree_item_by_id(
                current_id
            )
            if selected is not None:
                editor.tree.setCurrentItem(selected)

        command = build_document_delta(
            editor.document_controller,
            capture,
            label="Paste Shared Toolbox",
            selection_before=selection_before,
            selection_after=editor.current_item_id
        )
        if command is not None:
            editor.command_history.push_applied(command)

        try:
            editor._sync_property_baseline()
        except Exception:
            pass

        editor.status.setText(
            "Pasted shared toolbox ({0}). Apply or Accept to save.".format(
                mode
            )
        )

    # ------------------------------------------------------------------
    # Parameter share / paste
    # ------------------------------------------------------------------

    def share_selected(self, target_item=None):
        editor = self.editor
        current = target_item or editor.tree.currentItem()
        if current is None:
            return

        editor.tree.setCurrentItem(current)
        editor.sync_working_from_tree()
        item_id = editor.item_data(
            current,
            QtCore.Qt.UserRole + 1
        )
        data = editor.item_cache.get(item_id)

        if data is None:
            return

        payload_data = copy.deepcopy(data)
        label = data.get(
            "label",
            data.get("name", "Parameter")
        )
        self._start_share_operation(
            "Encrypting and sharing parameter...",
            lambda: share_data(
                "item",
                payload_data
            ),
            lambda code: self._share_code_ready(
                code,
                label
            )
        )

    def paste_shared_selected(self):
        code = self._clipboard_share_code()
        if not code:
            return

        self._start_share_operation(
            "Downloading and decrypting shared parameter...",
            lambda: fetch_shared_data(code),
            self._shared_item_ready
        )

    def _shared_item_ready(self, payload):
        editor = self.editor
        if payload.get("type") != "item":
            QtGui.QMessageBox.warning(
                editor,
                "Script Toolbox Share",
                "This STB1 code contains a full toolbox. "
                "Use the Paste Shared button beside Import/Export."
            )
            editor.status.setText(
                "Shared data was not a parameter."
            )
            return

        raw = payload.get("data")
        if not isinstance(raw, dict):
            QtGui.QMessageBox.warning(
                editor,
                "Script Toolbox Share",
                "Shared parameter data is invalid."
            )
            return

        kind = text_type(
            raw.get("kind", "button")
        ).lower()
        source = create_item(
            kind,
            copy.deepcopy(raw)
        )

        editor.sync_working_from_tree()
        clone = editor._clone_data(
            source,
            editor._used_names()
        )

        previous_label = getattr(
            editor,
            "_next_tree_label",
            None
        )
        editor._next_tree_label = "Paste Shared Parameter"

        try:
            tree_item = editor._insert_cloned_tree_item(
                clone,
                sibling=False
            )
            editor.tree.setCurrentItem(tree_item)
            editor.fix_tree_structure()
            editor.tree_changed()
        finally:
            if getattr(
                editor,
                "_next_tree_label",
                None
            ) == "Paste Shared Parameter":
                editor._next_tree_label = previous_label

        editor.status.setText(
            "Pasted shared parameter: {0}. Apply or Accept to save.".format(
                clone.get(
                    "label",
                    clone.get("name", "Parameter")
                )
            )
        )


def install_share_controller(editor):
    """Create one ShareController for an editor instance."""
    controller = getattr(
        editor,
        "share_controller",
        None
    )
    if controller is None:
        controller = ShareController(editor)
        editor.share_controller = controller
    return controller


def build_share_interface_editor_class(base_class):
    """Compatibility wrapper for older direct builder imports.

    Active Script Toolbox composition installs ShareController through the
    presentation adapter instead of adding this inheritance layer.
    """

    class InterfaceEditor(base_class):

        def __init__(self, toolbox, parent=None):
            install_share_controller(self)
            base_class.__init__(
                self,
                toolbox,
                parent=parent
            )

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

    InterfaceEditor.__name__ = "InterfaceEditor"
    return InterfaceEditor


__all__ = [
    "ShareController",
    "install_share_controller",
    "build_share_interface_editor_class",
]
