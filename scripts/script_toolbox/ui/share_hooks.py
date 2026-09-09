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
from .icon_button import ICON_BUTTON_COMPACT
from .icon_button import create_icon_button


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


def _layout_for_widget(layout, target):
    if layout is None:
        return None, -1

    for index in range(layout.count()):
        entry = layout.itemAt(index)
        if entry is None:
            continue

        if entry.widget() is target:
            return layout, index

        child_layout = entry.layout()
        if child_layout is not None:
            found_layout, found_index = _layout_for_widget(
                child_layout,
                target
            )
            if found_layout is not None:
                return found_layout, found_index

    return None, -1


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


def build_share_interface_editor_class(base_class):
    class InterfaceEditor(base_class):

        def __init__(self, toolbox, parent=None):
            self._share_workers = []
            self._share_callbacks = {}
            self.import_button = None
            self.export_button = None
            self.share_paste_button = None
            self.share_button = None
            base_class.__init__(
                self,
                toolbox,
                parent=parent
            )

        # --------------------------------------------------------------
        # UI integration
        # --------------------------------------------------------------

        def _icon_button(
            self,
            icon_name,
            tooltip,
            callback
        ):
            button = create_icon_button(
                icon_name,
                tooltip,
                callback,
                parent=self,
                preset=ICON_BUTTON_COMPACT
            )

            if icon_name == "import":
                self.import_button = button
            elif icon_name == "export":
                self.export_button = button

            return button

        def build_ui(self):
            base_class.build_ui(self)
            self._install_share_buttons()

        def _install_share_buttons(self):
            export_button = self.export_button
            if export_button is None:
                return

            layout, index = _layout_for_widget(
                self.layout(),
                export_button
            )
            if layout is None:
                return

            self.share_paste_button = create_icon_button(
                "cloud-download",
                "Paste Shared Toolbox from Clipboard",
                self.paste_shared_settings,
                parent=self,
                preset=ICON_BUTTON_COMPACT
            )
            self.share_button = create_icon_button(
                "cloud-upload",
                "Share Toolbox and Copy STB1 Code",
                self.share_settings,
                parent=self,
                preset=ICON_BUTTON_COMPACT
            )

            layout.insertWidget(
                index + 1,
                self.share_paste_button
            )
            layout.insertWidget(
                index + 2,
                self.share_button
            )

        def show_tree_context_menu(self, point):
            item = self.tree.itemAt(point)
            if item is not None:
                self.tree.setCurrentItem(item)

            menu = QtGui.QMenu(self.tree)
            undo_action = menu.addAction("Undo")
            redo_action = menu.addAction("Redo")
            undo_action.setEnabled(bool(self.undo_stack))
            redo_action.setEnabled(bool(self.redo_stack))
            menu.addSeparator()

            copy_action = menu.addAction("Copy")
            paste_action = menu.addAction("Paste")
            duplicate_action = menu.addAction("Duplicate")
            paste_action.setEnabled(
                self.clipboard_item is not None
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
                self.tree.viewport().mapToGlobal(point)
            )

            if action == undo_action:
                self.undo()
            elif action == redo_action:
                self.redo()
            elif action == copy_action:
                self.copy_selected()
            elif action == paste_action:
                self.paste_selected()
            elif action == duplicate_action:
                self.duplicate_selected(item)
            elif action == share_action:
                self.share_selected(item)
            elif action == paste_shared_action:
                self.paste_shared_selected()
            elif action == delete_action:
                self.delete_selected()

        # --------------------------------------------------------------
        # Worker helpers
        # --------------------------------------------------------------

        def _start_share_operation(
            self,
            status_text,
            operation,
            callback
        ):
            worker = _ShareWorker(
                operation,
                self
            )
            self._share_workers.append(worker)
            self._share_callbacks[worker] = callback
            worker.completed.connect(
                lambda result, current=worker: self._share_operation_finished(
                    current,
                    result
                )
            )
            self.status.setText(status_text)
            worker.start()

        def _share_operation_finished(
            self,
            worker,
            result
        ):
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
                self.status.setText("Share operation failed.")
                QtGui.QMessageBox.critical(
                    self,
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
            try:
                return extract_share_code(
                    _clipboard_text()
                )
            except ShareError as exc:
                QtGui.QMessageBox.warning(
                    self,
                    "Script Toolbox Share",
                    text_type(exc)
                )
                return None

        def _share_code_ready(self, code, label):
            _set_clipboard_text(code)
            self.status.setText(
                "{0} shared. STB1 code copied to clipboard.".format(
                    label
                )
            )

        # --------------------------------------------------------------
        # Whole toolbox share / paste
        # --------------------------------------------------------------

        def share_settings(self):
            self.sync_working_from_tree()

            if not self.validate_internal_names():
                return

            document = copy.deepcopy(
                self.working
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
            if payload.get("type") != "config":
                QtGui.QMessageBox.warning(
                    self,
                    "Script Toolbox Share",
                    "This STB1 code contains a parameter, not a full toolbox. "
                    "Use Paste Shared from the parameter context menu."
                )
                self.status.setText(
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
                self,
                "Paste Shared Toolbox",
                "Paste mode:",
                modes,
                0,
                False
            )

            if isinstance(choice, (tuple, list)):
                if len(choice) < 2 or not choice[1]:
                    self.status.setText(
                        "Shared toolbox paste cancelled."
                    )
                    return
                mode = text_type(choice[0])
            else:
                mode = text_type(choice)

            if not mode:
                return

            self.sync_working_from_tree()
            capture = DocumentCapture(
                self.document_controller
            )
            selection_before = self.current_item_id
            current_id = self.current_item_id

            if mode == "Replace Toolbox":
                self.working = normalize_document(
                    copy.deepcopy(imported)
                )
                current_id = None

            elif mode == "Append to Toolbox":
                used_names = self._used_names()
                for section in imported.get("sections", []):
                    self.working.setdefault(
                        "sections",
                        []
                    ).append(
                        self._clone_data(
                            section,
                            used_names
                        )
                    )

            else:
                current = self.tree.currentItem()
                target_tree = self.nearest_folder(current)

                if target_tree is None:
                    target_tree = self.ensure_root_folder()

                target_id = self.item_data(
                    target_tree,
                    self.ROLE_ID
                ) if hasattr(self, "ROLE_ID") else self.item_data(
                    target_tree,
                    QtCore.Qt.UserRole + 1
                )
                target = self.item_cache.get(target_id)

                if target is None:
                    QtGui.QMessageBox.warning(
                        self,
                        "Script Toolbox Share",
                        "Select a Folder before using Insert mode."
                    )
                    return

                used_names = self._used_names()
                target.setdefault("items", [])
                for section in imported.get("sections", []):
                    target["items"].append(
                        self._clone_data(
                            section,
                            used_names
                        )
                    )
                current_id = target_id

            self.populate_tree()
            if current_id:
                selected = self.tree_item_by_id(
                    current_id
                )
                if selected is not None:
                    self.tree.setCurrentItem(selected)

            command = build_document_delta(
                self.document_controller,
                capture,
                label="Paste Shared Toolbox",
                selection_before=selection_before,
                selection_after=self.current_item_id
            )
            if command is not None:
                self.command_history.push_applied(command)

            try:
                self._sync_property_baseline()
            except Exception:
                pass

            self.status.setText(
                "Pasted shared toolbox ({0}). Apply or Accept to save.".format(
                    mode
                )
            )

        # --------------------------------------------------------------
        # Parameter share / paste
        # --------------------------------------------------------------

        def share_selected(self, target_item=None):
            current = target_item or self.tree.currentItem()
            if current is None:
                return

            self.tree.setCurrentItem(current)
            self.sync_working_from_tree()
            item_id = self.item_data(
                current,
                QtCore.Qt.UserRole + 1
            )
            data = self.item_cache.get(item_id)

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
            if payload.get("type") != "item":
                QtGui.QMessageBox.warning(
                    self,
                    "Script Toolbox Share",
                    "This STB1 code contains a full toolbox. "
                    "Use the Paste Shared button beside Import/Export."
                )
                self.status.setText(
                    "Shared data was not a parameter."
                )
                return

            raw = payload.get("data")
            if not isinstance(raw, dict):
                QtGui.QMessageBox.warning(
                    self,
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

            self.sync_working_from_tree()
            clone = self._clone_data(
                source,
                self._used_names()
            )

            previous_label = getattr(
                self,
                "_next_tree_label",
                None
            )
            self._next_tree_label = "Paste Shared Parameter"

            try:
                tree_item = self._insert_cloned_tree_item(
                    clone,
                    sibling=False
                )
                self.tree.setCurrentItem(tree_item)
                self.fix_tree_structure()
                self.tree_changed()
            finally:
                if getattr(
                    self,
                    "_next_tree_label",
                    None
                ) == "Paste Shared Parameter":
                    self._next_tree_label = previous_label

            self.status.setText(
                "Pasted shared parameter: {0}. Apply or Accept to save.".format(
                    clone.get(
                        "label",
                        clone.get("name", "Parameter")
                    )
                )
            )

    InterfaceEditor.__name__ = "InterfaceEditor"
    return InterfaceEditor


__all__ = [
    "build_share_interface_editor_class",
]
