# -*- coding: utf-8 -*-
from __future__ import print_function

import copy
import os

from ..compat import QtCore
from ..compat import QtGui
from ..core.config import deserialize_config
from ..core.config import import_config
from ..core.config import serialize_config
from ..core.config_schema import ConfigSchemaError
from ..core.config_schema import UnsupportedConfigVersionError
from ..core.editor_commands import DocumentCapture
from ..core.editor_commands import build_document_delta
from ..core.logging_utils import get_logger
from ..model import ItemValidationError
from ..model import normalize_document
from ..pycompat import text_type


_LOGGER = get_logger()
_EDITOR_MARKER = "_script_toolbox_template_transfer_editor"
_ROLE_ID = QtCore.Qt.UserRole + 1

_IMPORT_MODES = (
    "Replace Toolbox",
    "Append to Toolbox",
    "Insert into Selected Folder",
)


def _clipboard_text():
    return text_type(
        QtGui.QApplication.clipboard().text() or ""
    )


def _set_clipboard_text(value):
    QtGui.QApplication.clipboard().setText(
        text_type(value)
    )


def _connect_menu_action(action, callback):
    action.triggered.connect(
        lambda checked=False, current=callback: current()
    )


def _configure_menu_button(
    button,
    connected_callback,
    tooltip,
    actions
):
    """Convert an existing toolbar button into a menu-only QToolButton."""
    if button is None:
        return

    try:
        button.clicked.disconnect(
            connected_callback
        )
    except Exception:
        # Some bindings raise when no matching connection exists. InstantPopup
        # still prevents an implicit default action, so this is only cleanup.
        pass

    menu = QtGui.QMenu(
        button
    )

    for label, callback in actions:
        if label is None:
            menu.addSeparator()
            continue

        action = menu.addAction(
            label
        )
        _connect_menu_action(
            action,
            callback
        )

    button.setMenu(
        menu
    )
    button.setPopupMode(
        QtGui.QToolButton.InstantPopup
    )
    button.setToolTip(
        tooltip
    )


def _remove_redundant_share_buttons(editor):
    """Remove legacy whole-toolbox share buttons after menu integration."""
    layout = getattr(
        editor,
        "share_action_layout",
        None
    )

    for attribute in (
        "share_paste_button",
        "share_button",
    ):
        button = getattr(
            editor,
            attribute,
            None
        )
        if button is None:
            continue

        if layout is not None:
            try:
                layout.removeWidget(
                    button
                )
            except Exception:
                pass

        try:
            button.setParent(
                None
            )
            button.deleteLater()
        except Exception:
            try:
                button.hide()
            except Exception:
                pass

        setattr(
            editor,
            attribute,
            None
        )


def build_template_transfer_interface_editor_class(base_class):
    """Add menu-driven file/clipboard/share transfer to InterfaceEditor."""
    if getattr(
        base_class,
        _EDITOR_MARKER,
        False
    ):
        return base_class

    class TemplateTransferInterfaceEditor(base_class):

        def _icon_button(
            self,
            icon_name,
            tooltip,
            callback
        ):
            widget = base_class._icon_button(
                self,
                icon_name,
                tooltip,
                callback
            )

            if icon_name == "import":
                button = getattr(
                    self,
                    "import_button",
                    widget
                )
                _configure_menu_button(
                    button,
                    callback,
                    (
                        "Import\n"
                        "Choose how to import or paste a template."
                    ),
                    (
                        (
                            "Import Template from File...",
                            callback
                        ),
                        (
                            "Import Template from Clipboard",
                            self.import_template_from_clipboard
                        ),
                        (
                            None,
                            None
                        ),
                        (
                            "Paste Shared Toolbox from Clipboard",
                            self.paste_shared_settings
                        ),
                    )
                )

            elif icon_name == "export":
                _remove_redundant_share_buttons(
                    self
                )

                button = getattr(
                    self,
                    "export_button",
                    None
                )
                if button is None and isinstance(
                    widget,
                    QtGui.QToolButton
                ):
                    button = widget

                _configure_menu_button(
                    button,
                    callback,
                    (
                        "Export\n"
                        "Choose how to export, copy, or share the current template."
                    ),
                    (
                        (
                            "Export Template to File...",
                            callback
                        ),
                        (
                            "Copy Template to Clipboard",
                            self.copy_template_to_clipboard
                        ),
                        (
                            None,
                            None
                        ),
                        (
                            "Share Toolbox and Copy STB1 Code",
                            self.share_settings
                        ),
                    )
                )

            return widget

        def _choose_template_import_mode(self, title):
            choice = QtGui.QInputDialog.getItem(
                self,
                title,
                "Import mode:",
                list(_IMPORT_MODES),
                0,
                False
            )

            if isinstance(
                choice,
                (tuple, list)
            ):
                if len(choice) < 2 or not choice[1]:
                    return ""
                return text_type(
                    choice[0]
                )

            return text_type(
                choice or ""
            )

        def _apply_template_import(
            self,
            imported,
            mode,
            source_label
        ):
            """Apply one validated template through the active editor model."""
            if self.history_timer.isActive():
                self.commit_history(
                    sync_tree=False
                )

            self.sync_working_from_tree()
            capture = DocumentCapture(
                self.document_controller
            )
            selection_before = self.current_item_id
            current_id = self.current_item_id

            if mode == "Replace Toolbox":
                self.working = normalize_document(
                    copy.deepcopy(
                        imported
                    )
                )

            elif mode == "Append to Toolbox":
                used_names = self._used_names()
                for section in imported.get(
                    "sections",
                    []
                ):
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
                target_tree = self.nearest_section(
                    current
                )

                if target_tree is None:
                    target_tree = self.ensure_root_section()

                target_id = self.item_data(
                    target_tree,
                    _ROLE_ID
                )
                target = self.item_cache.get(
                    target_id
                )

                if target is None:
                    raise RuntimeError(
                        "Select a Folder before using Insert mode."
                    )

                used_names = self._used_names()
                target.setdefault(
                    "items",
                    []
                )
                for section in imported.get(
                    "sections",
                    []
                ):
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
                    self.tree.setCurrentItem(
                        selected
                    )

            command = build_document_delta(
                self.document_controller,
                capture,
                label="Import Toolbox",
                selection_before=selection_before,
                selection_after=self.current_item_id
            )
            if command is not None:
                self.command_history.push_applied(
                    command
                )

            try:
                self._sync_property_baseline()
            except Exception:
                pass

            self.status.setText(
                "Imported {0} ({1}). Apply or Accept to save.".format(
                    source_label,
                    mode
                )
            )

        def import_settings(self):
            result = QtGui.QFileDialog.getOpenFileName(
                self,
                "Import Script Toolbox Settings",
                "",
                "JSON Files (*.json);;All Files (*.*)"
            )
            path = self._dialog_path(
                result
            )
            if not path:
                return

            mode = self._choose_template_import_mode(
                "Import Script Toolbox Settings"
            )
            if not mode:
                return

            try:
                imported = import_config(
                    path
                )
                self._apply_template_import(
                    imported,
                    mode,
                    os.path.basename(path)
                )
            except Exception as exc:
                _LOGGER.debug(
                    "Template file import failed for %r.",
                    path,
                    exc_info=True
                )
                QtGui.QMessageBox.critical(
                    self,
                    "Import Failed",
                    text_type(exc)
                )

        def import_template_from_clipboard(self):
            try:
                raw_text = _clipboard_text()
            except Exception:
                _LOGGER.exception(
                    "Could not read the system clipboard for template import."
                )
                QtGui.QMessageBox.critical(
                    self,
                    "Import Template",
                    "Could not read the system clipboard."
                )
                return

            if not raw_text.strip():
                QtGui.QMessageBox.warning(
                    self,
                    "Import Template",
                    "Clipboard does not contain a template."
                )
                return

            try:
                imported = deserialize_config(
                    raw_text
                )
            except ValueError:
                _LOGGER.debug(
                    "Clipboard template import contains invalid JSON.",
                    exc_info=True
                )
                QtGui.QMessageBox.warning(
                    self,
                    "Import Template",
                    "Clipboard does not contain valid JSON."
                )
                return
            except UnsupportedConfigVersionError as exc:
                _LOGGER.debug(
                    "Clipboard template uses an unsupported schema version.",
                    exc_info=True
                )
                QtGui.QMessageBox.warning(
                    self,
                    "Import Template",
                    text_type(exc)
                )
                return
            except (ConfigSchemaError, ItemValidationError):
                _LOGGER.debug(
                    "Clipboard JSON is not a supported Script Toolbox template.",
                    exc_info=True
                )
                QtGui.QMessageBox.warning(
                    self,
                    "Import Template",
                    "Unsupported template format."
                )
                return
            except Exception:
                _LOGGER.exception(
                    "Unexpected clipboard template import failure."
                )
                QtGui.QMessageBox.critical(
                    self,
                    "Import Template",
                    "Could not import the template from the clipboard."
                )
                return

            mode = self._choose_template_import_mode(
                "Import Template from Clipboard"
            )
            if not mode:
                return

            try:
                self._apply_template_import(
                    imported,
                    mode,
                    "Clipboard"
                )
            except Exception:
                _LOGGER.exception(
                    "Could not apply the clipboard template."
                )
                QtGui.QMessageBox.critical(
                    self,
                    "Import Template",
                    "Could not import the template from the clipboard."
                )

        def copy_template_to_clipboard(self):
            self.sync_working_from_tree()

            if not self.validate_internal_names():
                return

            try:
                json_text = serialize_config(
                    self.working
                )
                _set_clipboard_text(
                    json_text
                )
            except Exception:
                _LOGGER.exception(
                    "Could not copy the current template to the clipboard."
                )
                QtGui.QMessageBox.critical(
                    self,
                    "Export Template",
                    "Could not copy the current template to the clipboard."
                )
                return

            self.status.setText(
                "Template copied to clipboard."
            )

    TemplateTransferInterfaceEditor.__name__ = "InterfaceEditor"
    setattr(
        TemplateTransferInterfaceEditor,
        _EDITOR_MARKER,
        True
    )
    return TemplateTransferInterfaceEditor


__all__ = [
    "build_template_transfer_interface_editor_class",
]
