# -*- coding: utf-8 -*-
from __future__ import print_function

import os

from ..compat import QtGui
from ..compat import QtCore
from ..integrations.base import STATUS_NOT_INSTALLED
from ..integrations.base import STATUS_UPDATE_REQUIRED
from ..integrations.config import get_integration_settings
from ..integrations.manager import DccIntegrationManager
from ..pycompat import text_type
from ..style import metrics
from .collapsible_folder import CollapsibleSection
from .update_ui import update_jobs
from .settings_components import build_page_header
from .settings_components import configure_settings_scroll_area
from .settings_components import mark_secondary_text


class IntegrationJob(QtCore.QThread):
    completed = QtCore.Signal(object)

    def __init__(self, callback):
        owner = update_jobs()
        QtCore.QThread.__init__(self, owner)
        self.callback = callback
        owner.retain(self)

    def run(self):
        try:
            result = {"value": self.callback()}
        except Exception as exc:
            result = {"error": text_type(exc)}
        self.completed.emit(result)


class DccIntegrationsPage(QtGui.QWidget):
    """Compact Settings page for per-version DCC integration actions."""

    def __init__(self, parent=None, manager=None):
        QtGui.QWidget.__init__(self, parent)
        self.manager = manager or DccIntegrationManager()
        self.installations = {}
        self.rows = {}
        self._scan_job = None
        self._operation_job = None
        self._profile_roots = {}
        self._collapsed_state = {}

        root = QtGui.QVBoxLayout(self)
        root.setContentsMargins(*metrics.SETTINGS_PAGE_MARGINS)
        root.setSpacing(metrics.SETTINGS_PAGE_SPACING)

        root.addWidget(
            build_page_header(
                "DCC Integrations",
                "Detect installed DCC applications and manage Script Toolbox "
                "integration for each host version.",
                parent=self
            )
        )

        actions = QtGui.QHBoxLayout()
        actions.setSpacing(metrics.SETTINGS_ACTION_SPACING)
        self.scan_button = QtGui.QPushButton("Scan DCCs")
        self.scan_button.clicked.connect(self.scan)
        actions.addWidget(self.scan_button)
        actions.addStretch(1)
        root.addLayout(actions)

        self.scroll = QtGui.QScrollArea(self)
        configure_settings_scroll_area(self.scroll)
        root.addWidget(self.scroll, 1)

        self.container = QtGui.QWidget()
        self.container.setObjectName("SettingsScrollContent")
        self.container_layout = QtGui.QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(*metrics.MARGINS_NONE)
        self.container_layout.setSpacing(metrics.SETTINGS_SECTION_SPACING)
        self.scroll.setWidget(self.container)

        QtCore.QTimer.singleShot(0, self.scan)

    def _clear_cards(self):
        self.rows = {}
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    @staticmethod
    def _default_options(adapter, installation):
        if hasattr(installation, "scanned_options"):
            return installation.scanned_options
        stored = get_integration_settings(
            installation.dcc,
            installation.version,
            profile_id=installation.profile_id
        )
        return adapter.normalize_options(
            stored or {}
        )

    @staticmethod
    def _supports_profile_locations(adapter):
        return callable(
            getattr(
                adapter,
                "profile_roots",
                None
            )
        )

    @staticmethod
    def _target_count_text(adapter, count):
        if DccIntegrationsPage._supports_profile_locations(
            adapter
        ):
            noun = "profile" if count == 1 else "profiles"
        else:
            noun = "version" if count == 1 else "versions"
        return "{0} {1}".format(count, noun)

    def _collapse_key(self, adapter_key, version=None):
        if version is None:
            return "dcc:{0}".format(adapter_key)
        return "dcc:{0}:version:{1}".format(
            adapter_key,
            text_type(version)
        )

    def _collapsed_value(self, key, default):
        return bool(self._collapsed_state.get(key, default))

    def _remember_collapsed(self, key, collapsed):
        self._collapsed_state[key] = bool(collapsed)

    def _connect_collapse_state(self, section, key):
        section.collapsedChanged.connect(
            lambda collapsed, state_key=key: self._remember_collapsed(
                state_key,
                collapsed
            )
        )

    def scan(self, *args):
        if self._scan_job is not None and self._scan_job.isRunning():
            return
        self.scan_button.setEnabled(False)
        self.scan_button.setText("Scanning...")
        self._scan_job = IntegrationJob(self.manager.scan_details)
        self._scan_job.completed.connect(self._scan_finished)
        self._scan_job.start()

    @QtCore.Slot(object)
    def _scan_finished(self, result):
        self.scan_button.setEnabled(True)
        self.scan_button.setText("Scan DCCs")
        if result.get("error"):
            self._show_error("DCC Scan Failed", result["error"])
            return
        self.installations = result["value"]["installations"]
        self._profile_roots = result["value"]["roots"]
        self._rebuild_cards()

    def _rebuild_cards(self):
        self._clear_cards()

        for adapter in self.manager.adapters():
            self.container_layout.addWidget(
                self._build_adapter_section(adapter)
            )

        self.container_layout.addStretch(1)

    def _adapter_title(self, adapter, installations):
        if not installations:
            suffix = "Not detected"
        else:
            suffix = self._target_count_text(adapter, len(installations))
            if not adapter.integration_available:
                suffix += " | Detection only"

        return "{0}  |  {1}".format(
            adapter.display_name,
            suffix
        )

    def _build_adapter_section(self, adapter):
        installations = self.installations.get(adapter.key, [])
        key = self._collapse_key(adapter.key)
        section = CollapsibleSection(
            title=self._adapter_title(adapter, installations),
            collapsed=self._collapsed_value(
                key,
                adapter.key != "maya"
            ),
            nested=False,
            content_margins=metrics.RUNTIME_FOLDER_CONTENT_MARGINS,
            content_spacing=metrics.RUNTIME_FOLDER_CONTENT_SPACING,
            parent=self.container
        )
        self._connect_collapse_state(section, key)
        layout = section.content_layout

        if self._supports_profile_locations(
            adapter
        ):
            self._add_profile_locations(
                adapter,
                layout,
                section.content
            )

        if not installations:
            empty = mark_secondary_text(
                QtGui.QLabel(
                    "No installed versions detected.",
                    section.content
                )
            )
            empty.setWordWrap(True)
            layout.addWidget(empty)
            return section

        if adapter.integration_available and adapter.key == "maya":
            if len(installations) > 1:
                self._add_install_all_row(layout, section.content)

        if not adapter.integration_available:
            note = mark_secondary_text(
                QtGui.QLabel(
                    "Automatic integration is not implemented for this DCC yet.",
                    section.content
                )
            )
            note.setWordWrap(True)
            layout.addWidget(note)

        for installation in installations:
            layout.addWidget(
                self._build_installation_section(
                    adapter,
                    installation,
                    section.content
                )
            )

        return section

    def _add_profile_locations(
        self,
        adapter,
        layout,
        parent
    ):
        roots = self._profile_roots.get(adapter.key, [])
        state_key = "dcc:{0}:profile-locations".format(
            adapter.key
        )
        section = CollapsibleSection(
            title="Profile locations  |  {0}".format(
                len(roots)
            ),
            collapsed=self._collapsed_value(
                state_key,
                True
            ),
            nested=True,
            content_margins=metrics.RUNTIME_FOLDER_CONTENT_MARGINS,
            content_spacing=metrics.RUNTIME_FOLDER_CONTENT_SPACING,
            parent=parent
        )
        self._connect_collapse_state(
            section,
            state_key
        )

        for profile in roots:
            row = QtGui.QHBoxLayout()
            row.setSpacing(
                metrics.SETTINGS_ACTION_SPACING
            )

            label = mark_secondary_text(
                QtGui.QLabel(
                    "{0}: {1}".format(
                        profile.get("label") or "Custom",
                        profile.get("path") or ""
                    ),
                    section.content
                )
            )
            label.setWordWrap(True)
            row.addWidget(label, 1)

            if profile.get(
                "removable",
                False
            ):
                remove_button = QtGui.QPushButton(
                    "Remove",
                    section.content
                )
                remove_button.clicked.connect(
                    lambda checked=False,
                    dcc_key=adapter.key,
                    display_name=adapter.display_name,
                    profile_id=profile.get("id"):
                    self._remove_profile_path(
                        dcc_key,
                        display_name,
                        profile_id
                    )
                )
                row.addWidget(
                    remove_button
                )

            section.content_layout.addLayout(
                row
            )

        add_row = QtGui.QHBoxLayout()
        add_row.setSpacing(
            metrics.SETTINGS_ACTION_SPACING
        )
        add_button = QtGui.QPushButton(
            "Add profile path...",
            section.content
        )
        add_button.clicked.connect(
            lambda checked=False,
            dcc_key=adapter.key,
            display_name=adapter.display_name:
            self._add_profile_path(
                dcc_key,
                display_name
            )
        )
        add_row.addWidget(add_button)
        add_row.addStretch(1)
        section.content_layout.addLayout(
            add_row
        )

        layout.addWidget(section)

    def _add_profile_path(
        self,
        dcc_key,
        display_name
    ):
        selected = QtGui.QFileDialog.getExistingDirectory(
            self,
            "Add {0} Profile Path".format(
                display_name
            )
        )
        selected = text_type(
            selected or ""
        ).strip()
        if not selected:
            return

        normalized = os.path.normpath(
            selected
        )
        suggested = os.path.basename(
            normalized.rstrip("\\/")
        ) or "Custom"

        label, accepted = QtGui.QInputDialog.getText(
            self,
            "{0} Profile Name".format(
                display_name
            ),
            "Name:",
            QtGui.QLineEdit.Normal,
            suggested
        )
        if not accepted:
            return

        label = (
            text_type(
                label or ""
            ).strip() or
            suggested
        )
        try:
            self.manager.add_profile_root(
                dcc_key,
                normalized,
                label=label
            )
        except Exception as exc:
            self._show_error(
                "Add Profile Path Failed",
                exc
            )
            return
        self.scan()

    def _remove_profile_path(
        self,
        dcc_key,
        display_name,
        profile_id
    ):
        answer = QtGui.QMessageBox.question(
            self,
            "Remove Profile Path",
            (
                "Stop scanning this {0} profile path?\n\n"
                "Installed Script Toolbox integration must be "
                "uninstalled first."
            ).format(
                display_name
            ),
            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
            QtGui.QMessageBox.No
        )
        if answer != QtGui.QMessageBox.Yes:
            return

        try:
            self.manager.remove_profile_root(
                dcc_key,
                profile_id
            )
        except Exception as exc:
            self._show_error(
                "Remove Profile Path Failed",
                exc
            )
            return
        self.scan()

    def _add_install_all_row(self, layout, parent):
        row = QtGui.QHBoxLayout()
        row.setSpacing(metrics.SETTINGS_ACTION_SPACING)

        label = mark_secondary_text(
            QtGui.QLabel("All profiles:", parent)
        )
        shelf = QtGui.QCheckBox("Shelf", parent)
        shelf.setChecked(True)
        menu = QtGui.QCheckBox("Main Menu", parent)
        menu.setChecked(True)
        button = QtGui.QPushButton("Install to all", parent)
        button.clicked.connect(
            lambda checked=False: self._install_all_maya(
                shelf.isChecked(),
                menu.isChecked()
            )
        )

        row.addWidget(label)
        row.addWidget(shelf)
        row.addWidget(menu)
        row.addStretch(1)
        row.addWidget(button)
        layout.addLayout(row)

    def _build_installation_section(self, adapter, installation, parent):
        status = installation.scanned_status
        key = self._collapse_key(
            installation.dcc,
            installation.key
        )
        section = CollapsibleSection(
            title="{0} - {1}  |  {2}".format(
                installation.version,
                installation.profile_label,
                status.state
            ),
            collapsed=self._collapsed_value(key, True),
            nested=True,
            content_margins=metrics.RUNTIME_FOLDER_CONTENT_MARGINS,
            content_spacing=metrics.RUNTIME_FOLDER_CONTENT_SPACING,
            parent=parent
        )
        self._connect_collapse_state(section, key)
        layout = section.content_layout

        if status.message:
            detail_label = mark_secondary_text(
                QtGui.QLabel(status.message, section.content)
            )
            detail_label.setWordWrap(True)
            layout.addWidget(detail_label)

        if installation.install_path:
            install_path = mark_secondary_text(
                QtGui.QLabel(
                    "Install: {0}".format(installation.install_path),
                    section.content
                )
            )
            install_path.setWordWrap(True)
            layout.addWidget(install_path)

        if installation.user_config_path:
            user_path = mark_secondary_text(
                QtGui.QLabel(
                    "User config: {0}".format(
                        installation.user_config_path
                    ),
                    section.content
                )
            )
            user_path.setWordWrap(True)
            layout.addWidget(user_path)

        row = {
            "installation": installation,
            "status": status,
        }
        self.rows[installation.key] = row

        if not adapter.integration_available:
            return section

        options = self._default_options(
            adapter,
            installation
        )
        component_status = mark_secondary_text(
            QtGui.QLabel(
                adapter.component_status_text(
                    status,
                    options
                ),
                section.content
            )
        )
        component_status.setWordWrap(True)
        layout.addWidget(component_status)

        options_row = QtGui.QHBoxLayout()
        options_row.setSpacing(metrics.SETTINGS_ACTION_SPACING)
        option_widgets = {}

        for option_key, label, unused_default in adapter.option_definitions():
            checkbox = QtGui.QCheckBox(
                label,
                section.content
            )
            checkbox.setChecked(
                bool(options.get(option_key))
            )
            option_widgets[option_key] = checkbox
            options_row.addWidget(checkbox)

        options_row.addStretch(1)
        layout.addLayout(options_row)

        row["option_widgets"] = option_widgets

        buttons = QtGui.QHBoxLayout()
        buttons.setSpacing(metrics.SETTINGS_ACTION_SPACING)
        if status.state == STATUS_NOT_INSTALLED:
            primary_label = "Install"
        elif status.state == STATUS_UPDATE_REQUIRED:
            primary_label = "Update"
        else:
            primary_label = "Apply Changes"

        primary = QtGui.QPushButton(primary_label)
        repair = QtGui.QPushButton("Repair")
        uninstall = QtGui.QPushButton("Uninstall")
        repair.setEnabled(status.state != STATUS_NOT_INSTALLED)
        uninstall.setEnabled(status.state != STATUS_NOT_INSTALLED)

        primary.clicked.connect(
            lambda checked=False, item=installation: self._install(item)
        )
        repair.clicked.connect(
            lambda checked=False, item=installation: self._repair(item)
        )
        uninstall.clicked.connect(
            lambda checked=False, item=installation: self._uninstall(item)
        )

        buttons.addWidget(primary)
        buttons.addWidget(repair)
        buttons.addWidget(uninstall)
        buttons.addStretch(1)
        layout.addLayout(buttons)
        return section

    def _options_for(self, installation):
        row = self.rows[installation.key]
        widgets = row.get(
            "option_widgets",
            {}
        )
        return {
            key: widget.isChecked()
            for key, widget in widgets.items()
        }

    def _show_error(self, title, exc):
        QtGui.QMessageBox.critical(
            self,
            title,
            text_type(exc)
        )

    def _start_operation(self, operation, installation, options=None):
        if self._operation_job is not None and self._operation_job.isRunning():
            return
        self._operation_target = installation
        self.container.setEnabled(False)
        self.scan_button.setEnabled(False)
        self._operation_job = IntegrationJob(lambda: self.manager.files_operation(
            operation, installation, options=options))
        self._operation_job.completed.connect(self._operation_finished)
        self._operation_job.start()

    @QtCore.Slot(object)
    def _operation_finished(self, result):
        self.container.setEnabled(True)
        if result.get("error"):
            self._show_error("DCC Integration Failed", result["error"])
        else:
            # Native DCC API always stays on the Qt/main thread.
            self.manager.sync_live(self._operation_target)
        self.scan()

    def _install(self, installation):
        self._start_operation("install", installation, self._options_for(installation))

    def _repair(self, installation):
        self._start_operation("repair", installation)

    def _uninstall(self, installation):
        answer = QtGui.QMessageBox.question(
            self,
            "Uninstall Integration",
            "Remove Script Toolbox integration from {0} {1}?".format(
                installation.display_name,
                installation.version
            ),
            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
            QtGui.QMessageBox.No
        )
        if answer != QtGui.QMessageBox.Yes:
            return

        self._start_operation("uninstall", installation)

    def _install_all_maya(self, shelf, main_menu):
        if self._operation_job is not None and self._operation_job.isRunning():
            return
        manager = self.manager
        targets = list(self.installations.get("maya", []))
        options = {"shelf": bool(shelf), "main_menu": bool(main_menu), "auto_open": False}

        def install_files():
            results = []
            for target in targets:
                try:
                    status = manager.files_operation("install", target, options)
                    results.append((target, status, None))
                except Exception as exc:
                    results.append((target, None, text_type(exc)))
            return results

        self.container.setEnabled(False)
        self.scan_button.setEnabled(False)
        self._operation_job = IntegrationJob(install_files)
        self._operation_job.completed.connect(self._bulk_install_finished)
        self._operation_job.start()

    @QtCore.Slot(object)
    def _bulk_install_finished(self, result):
        self.container.setEnabled(True)
        if result.get("error"):
            self._show_error("Maya Integration Failed", result["error"])
            self.scan()
            return
        results = result["value"]
        for installation, status, error in results:
            if error is None:
                self.manager.sync_live(installation)
        lines = []
        failures = 0
        for installation, status, error in results:
            if error is not None:
                failures += 1
                lines.append(
                    "{0}: failed - {1}".format(
                        "{0} - {1}".format(
                            installation.version,
                            installation.profile_label
                        ),
                        text_type(error)
                    )
                )
            else:
                lines.append(
                    "{0}: {1}".format(
                        "{0} - {1}".format(
                            installation.version,
                            installation.profile_label
                        ),
                        status.state
                    )
                )

        message = "\n".join(lines) or "No Maya installations detected."
        if failures:
            QtGui.QMessageBox.warning(
                self,
                "Maya Integration Results",
                message
            )
        else:
            QtGui.QMessageBox.information(
                self,
                "Maya Integration Results",
                message
            )
        self.scan()


__all__ = ["DccIntegrationsPage"]
