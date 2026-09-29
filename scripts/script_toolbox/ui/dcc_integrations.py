# -*- coding: utf-8 -*-
from __future__ import print_function

import os

from ..compat import QtGui
from ..integrations.base import STATUS_NOT_INSTALLED
from ..integrations.base import STATUS_UPDATE_REQUIRED
from ..integrations.config import get_integration_settings
from ..integrations.manager import DccIntegrationManager
from ..pycompat import text_type
from ..style import metrics
from .collapsible_folder import CollapsibleSection
from .settings_components import build_page_header
from .settings_components import configure_settings_scroll_area
from .settings_components import mark_secondary_text


class DccIntegrationsPage(QtGui.QWidget):
    """Compact Settings page for per-version DCC integration actions."""

    def __init__(self, parent=None, manager=None):
        QtGui.QWidget.__init__(self, parent)
        self.manager = manager or DccIntegrationManager()
        self.installations = {}
        self.rows = {}
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

        self.scan()

    def _clear_cards(self):
        self.rows = {}
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    @staticmethod
    def _default_options(installation):
        stored = get_integration_settings(
            installation.dcc,
            installation.version,
            profile_id=installation.profile_id
        )
        if stored is None:
            stored = {}
        return {
            "shelf": bool(stored.get("shelf", True)),
            "main_menu": bool(stored.get("main_menu", True)),
            "auto_open": bool(stored.get("auto_open", False)),
        }

    @staticmethod
    def _target_count_text(adapter, count):
        if adapter.key == "maya":
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
        self.scan_button.setEnabled(False)
        try:
            self.installations = self.manager.scan()
            self._rebuild_cards()
        finally:
            self.scan_button.setEnabled(True)

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

        if adapter.key == "maya":
            self._add_maya_profile_locations(
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

    def _add_maya_profile_locations(self, layout, parent):
        roots = self.manager.profile_roots("maya")
        section = CollapsibleSection(
            title="Profile locations  |  {0}".format(len(roots)),
            collapsed=self._collapsed_value(
                "dcc:maya:profile-locations",
                True
            ),
            nested=True,
            content_margins=metrics.RUNTIME_FOLDER_CONTENT_MARGINS,
            content_spacing=metrics.RUNTIME_FOLDER_CONTENT_SPACING,
            parent=parent
        )
        self._connect_collapse_state(
            section,
            "dcc:maya:profile-locations"
        )

        for profile in roots:
            row = QtGui.QHBoxLayout()
            row.setSpacing(metrics.SETTINGS_ACTION_SPACING)

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

            if profile.get("removable", False):
                remove_button = QtGui.QPushButton(
                    "Remove",
                    section.content
                )
                remove_button.clicked.connect(
                    lambda checked=False, profile_id=profile.get("id"):
                    self._remove_maya_profile_path(profile_id)
                )
                row.addWidget(remove_button)

            section.content_layout.addLayout(row)

        add_row = QtGui.QHBoxLayout()
        add_row.setSpacing(metrics.SETTINGS_ACTION_SPACING)
        add_button = QtGui.QPushButton(
            "Add profile path...",
            section.content
        )
        add_button.clicked.connect(self._add_maya_profile_path)
        add_row.addWidget(add_button)
        add_row.addStretch(1)
        section.content_layout.addLayout(add_row)

        layout.addWidget(section)

    def _add_maya_profile_path(self, *args):
        selected = QtGui.QFileDialog.getExistingDirectory(
            self,
            "Add Maya Profile Path"
        )
        selected = text_type(selected or "").strip()
        if not selected:
            return

        normalized = os.path.normpath(selected)
        suggested = os.path.basename(
            normalized.rstrip("\\/")
        ) or "Custom"

        label, accepted = QtGui.QInputDialog.getText(
            self,
            "Maya Profile Name",
            "Name:",
            QtGui.QLineEdit.Normal,
            suggested
        )
        if not accepted:
            return

        label = text_type(label or "").strip() or suggested
        try:
            self.manager.add_profile_root(
                "maya",
                normalized,
                label=label
            )
        except Exception as exc:
            self._show_error("Add Profile Path Failed", exc)
            return
        self.scan()

    def _remove_maya_profile_path(self, profile_id):
        answer = QtGui.QMessageBox.question(
            self,
            "Remove Profile Path",
            "Stop scanning this Maya profile path?\n\n"
            "Installed Script Toolbox integration must be uninstalled first.",
            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
            QtGui.QMessageBox.No
        )
        if answer != QtGui.QMessageBox.Yes:
            return

        try:
            self.manager.remove_profile_root(
                "maya",
                profile_id
            )
        except Exception as exc:
            self._show_error("Remove Profile Path Failed", exc)
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
        status = self.manager.status(installation)
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

        options = self._default_options(installation)
        component_status = mark_secondary_text(
            QtGui.QLabel(
                "Loader: {0}    Shelf: {1}    Main Menu: {2}".format(
                    "OK" if status.loader else "Missing",
                    (
                        "OK" if status.shelf else "Missing"
                    ) if options["shelf"] else "Disabled",
                    (
                        "Registered" if status.main_menu else "Missing"
                    ) if options["main_menu"] else "Disabled"
                ),
                section.content
            )
        )
        component_status.setWordWrap(True)
        layout.addWidget(component_status)

        options_row = QtGui.QHBoxLayout()
        options_row.setSpacing(metrics.SETTINGS_ACTION_SPACING)

        shelf = QtGui.QCheckBox("Add to Shelf", section.content)
        shelf.setChecked(options["shelf"])
        menu = QtGui.QCheckBox("Add to Main Menu", section.content)
        menu.setChecked(options["main_menu"])
        auto_open = QtGui.QCheckBox("Open on startup", section.content)
        auto_open.setChecked(options["auto_open"])

        options_row.addWidget(shelf)
        options_row.addWidget(menu)
        options_row.addWidget(auto_open)
        options_row.addStretch(1)
        layout.addLayout(options_row)

        row.update({
            "shelf": shelf,
            "main_menu": menu,
            "auto_open": auto_open,
        })

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
        return {
            "shelf": row["shelf"].isChecked(),
            "main_menu": row["main_menu"].isChecked(),
            "auto_open": row["auto_open"].isChecked(),
        }

    def _show_error(self, title, exc):
        QtGui.QMessageBox.critical(
            self,
            title,
            text_type(exc)
        )

    def _install(self, installation):
        try:
            self.manager.install(
                installation,
                options=self._options_for(installation)
            )
        except Exception as exc:
            self._show_error("DCC Integration Failed", exc)
        self.scan()

    def _repair(self, installation):
        try:
            self.manager.repair(installation)
        except Exception as exc:
            self._show_error("Repair Failed", exc)
        self.scan()

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

        try:
            self.manager.uninstall(installation)
        except Exception as exc:
            self._show_error("Uninstall Failed", exc)
        self.scan()

    def _install_all_maya(self, shelf, main_menu):
        results = self.manager.install_all(
            "maya",
            options={
                "shelf": bool(shelf),
                "main_menu": bool(main_menu),
                "auto_open": False,
            }
        )
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
