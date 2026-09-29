# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtGui
from ..integrations.base import STATUS_NOT_INSTALLED
from ..integrations.base import STATUS_UPDATE_REQUIRED
from ..integrations.config import get_integration_settings
from ..integrations.manager import DccIntegrationManager
from ..pycompat import text_type
from ..style import metrics
from .settings_components import build_page_header
from .settings_components import build_simple_section
from .settings_components import configure_settings_scroll_area
from .settings_components import mark_secondary_text
from .settings_components import mark_status_text


class DccIntegrationsPage(QtGui.QWidget):
    """Settings page for detection and per-version DCC integration actions."""

    def __init__(self, parent=None, manager=None):
        QtGui.QWidget.__init__(self, parent)
        self.manager = manager or DccIntegrationManager()
        self.installations = {}
        self.rows = {}

        root = QtGui.QVBoxLayout(self)
        root.setContentsMargins(*metrics.SETTINGS_PAGE_MARGINS)
        root.setSpacing(metrics.SETTINGS_PAGE_SPACING)

        root.addWidget(
            build_page_header(
                "DCC Integrations",
                "Detect installed DCC applications and install Script Toolbox "
                "without copying bootstrap code into a Script Editor.",
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
            installation.version
        )
        if stored is None:
            stored = {}
        return {
            "shelf": bool(stored.get("shelf", True)),
            "main_menu": bool(stored.get("main_menu", True)),
            "auto_open": bool(stored.get("auto_open", False)),
        }

    def scan(self, *args):
        self.scan_button.setEnabled(False)
        try:
            self.installations = self.manager.scan()
            self._rebuild_cards()
        finally:
            self.scan_button.setEnabled(True)

    def _rebuild_cards(self):
        self._clear_cards()

        maya_installations = self.installations.get("maya", [])
        if len(maya_installations) > 1:
            self.container_layout.addWidget(
                self._build_install_all_section(maya_installations)
            )

        for adapter in self.manager.adapters():
            self.container_layout.addWidget(
                self._build_adapter_section(adapter)
            )

        self.container_layout.addStretch(1)

    def _build_adapter_section(self, adapter):
        installations = self.installations.get(adapter.key, [])
        section, layout = build_simple_section(
            adapter.display_name,
            nested=False,
            parent=self.container
        )

        capability = mark_secondary_text(
            QtGui.QLabel(
                "Supported: {0}    Detected: {1}    Integration available: {2}".format(
                    "Yes" if adapter.supported else "No",
                    "Yes" if installations else "No",
                    "Yes" if adapter.integration_available else "No"
                ),
                section
            )
        )
        capability.setWordWrap(True)
        layout.addWidget(capability)

        if not installations:
            empty = mark_secondary_text(
                QtGui.QLabel(
                    "No installed versions detected.",
                    section
                )
            )
            empty.setWordWrap(True)
            layout.addWidget(empty)
            return section

        for installation in installations:
            layout.addWidget(
                self._build_installation_section(
                    adapter,
                    installation,
                    section
                )
            )

        if not adapter.integration_available:
            note = mark_secondary_text(
                QtGui.QLabel(
                    "Detection is implemented. Automatic integration is not "
                    "implemented for this DCC yet.",
                    section
                )
            )
            note.setWordWrap(True)
            layout.addWidget(note)

        return section

    def _build_install_all_section(self, installations):
        section, layout = build_simple_section(
            "Install to all detected Maya versions",
            nested=False,
            parent=self.container
        )

        checks = QtGui.QHBoxLayout()
        checks.setSpacing(metrics.SETTINGS_ACTION_SPACING)
        shelf = QtGui.QCheckBox("Shelf")
        shelf.setChecked(True)
        menu = QtGui.QCheckBox("Main Menu")
        menu.setChecked(True)
        checks.addWidget(shelf)
        checks.addWidget(menu)
        checks.addStretch(1)
        layout.addLayout(checks)

        button_row = QtGui.QHBoxLayout()
        button_row.setSpacing(metrics.SETTINGS_ACTION_SPACING)
        button = QtGui.QPushButton("Install to all")
        button.clicked.connect(
            lambda checked=False: self._install_all_maya(
                shelf.isChecked(),
                menu.isChecked()
            )
        )
        button_row.addWidget(button)
        button_row.addStretch(1)
        layout.addLayout(button_row)
        return section

    def _build_installation_section(self, adapter, installation, parent):
        section, layout = build_simple_section(
            "Version {0}".format(installation.version),
            nested=True,
            parent=parent
        )

        if installation.install_path:
            install_path = mark_secondary_text(
                QtGui.QLabel(
                    "Install: {0}".format(installation.install_path),
                    section
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
                    section
                )
            )
            user_path.setWordWrap(True)
            layout.addWidget(user_path)

        status = self.manager.status(installation)
        status_label = mark_status_text(
            QtGui.QLabel(
                "Integration: {0}".format(status.state),
                section
            )
        )
        status_label.setWordWrap(True)
        layout.addWidget(status_label)

        if status.message:
            detail_label = mark_secondary_text(
                QtGui.QLabel(status.message, section)
            )
            detail_label.setWordWrap(True)
            layout.addWidget(detail_label)

        row = {
            "installation": installation,
            "status_label": status_label,
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
                section
            )
        )
        component_status.setWordWrap(True)
        layout.addWidget(component_status)

        shelf = QtGui.QCheckBox("Add to Shelf", section)
        shelf.setChecked(options["shelf"])
        menu = QtGui.QCheckBox("Add to Main Menu", section)
        menu.setChecked(options["main_menu"])
        auto_open = QtGui.QCheckBox(
            "Open ScriptToolbox on Maya startup",
            section
        )
        auto_open.setChecked(options["auto_open"])
        layout.addWidget(shelf)
        layout.addWidget(menu)
        layout.addWidget(auto_open)

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
                        installation.version,
                        text_type(error)
                    )
                )
            else:
                lines.append(
                    "{0}: {1}".format(
                        installation.version,
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
