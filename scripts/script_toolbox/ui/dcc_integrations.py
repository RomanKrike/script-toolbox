# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtGui
from ..integrations.base import STATUS_NOT_INSTALLED
from ..integrations.config import get_integration_settings
from ..integrations.manager import DccIntegrationManager
from ..pycompat import text_type


class DccIntegrationsPage(QtGui.QWidget):
    """Settings page for detection and per-version DCC integration actions."""

    def __init__(self, parent=None, manager=None):
        QtGui.QWidget.__init__(self, parent)
        self.manager = manager or DccIntegrationManager()
        self.installations = {}
        self.rows = {}

        root = QtGui.QVBoxLayout(self)
        root.setContentsMargins(4, 0, 0, 0)
        root.setSpacing(12)

        title = QtGui.QLabel("DCC Integrations")
        title.setObjectName("SettingsPageTitle")
        title_font = title.font()
        title_font.setBold(True)
        title_font.setPointSize(title_font.pointSize() + 2)
        title.setFont(title_font)
        root.addWidget(title)

        description = QtGui.QLabel(
            "Detect installed DCC applications and install Script Toolbox "
            "without copying bootstrap code into a Script Editor."
        )
        description.setObjectName("SettingsPageDescription")
        description.setWordWrap(True)
        root.addWidget(description)

        actions = QtGui.QHBoxLayout()
        self.scan_button = QtGui.QPushButton("Scan DCCs")
        self.scan_button.clicked.connect(self.scan)
        actions.addWidget(self.scan_button)
        actions.addStretch(1)
        root.addLayout(actions)

        self.scroll = QtGui.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QtGui.QFrame.NoFrame)
        root.addWidget(self.scroll, 1)

        self.container = QtGui.QWidget()
        self.container_layout = QtGui.QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(10)
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
                self._build_install_all_card(maya_installations)
            )

        for adapter in self.manager.adapters():
            installations = self.installations.get(adapter.key, [])
            group = QtGui.QGroupBox(adapter.display_name)
            layout = QtGui.QVBoxLayout(group)
            layout.setSpacing(8)

            capability = QtGui.QLabel(
                "Supported: {0}    Detected: {1}    Integration available: {2}".format(
                    "Yes" if adapter.supported else "No",
                    "Yes" if installations else "No",
                    "Yes" if adapter.integration_available else "No"
                )
            )
            capability.setWordWrap(True)
            layout.addWidget(capability)

            if not installations:
                empty = QtGui.QLabel("No installed versions detected.")
                empty.setWordWrap(True)
                layout.addWidget(empty)
            else:
                for installation in installations:
                    layout.addWidget(
                        self._build_installation_card(
                            adapter,
                            installation
                        )
                    )

            if installations and not adapter.integration_available:
                note = QtGui.QLabel(
                    "Detection is implemented. Automatic integration is not "
                    "implemented for this DCC yet."
                )
                note.setWordWrap(True)
                layout.addWidget(note)

            self.container_layout.addWidget(group)

        self.container_layout.addStretch(1)

    def _build_install_all_card(self, installations):
        card = QtGui.QGroupBox("Install to all detected Maya versions")
        layout = QtGui.QVBoxLayout(card)

        checks = QtGui.QHBoxLayout()
        shelf = QtGui.QCheckBox("Shelf")
        shelf.setChecked(True)
        menu = QtGui.QCheckBox("Main Menu")
        menu.setChecked(True)
        checks.addWidget(shelf)
        checks.addWidget(menu)
        checks.addStretch(1)
        layout.addLayout(checks)

        button = QtGui.QPushButton("Install to all")
        button.clicked.connect(
            lambda checked=False: self._install_all_maya(
                shelf.isChecked(),
                menu.isChecked()
            )
        )
        layout.addWidget(button)
        return card

    def _build_installation_card(self, adapter, installation):
        card = QtGui.QGroupBox(
            "{0} {1}".format(
                adapter.display_name,
                installation.version
            )
        )
        layout = QtGui.QVBoxLayout(card)
        layout.setSpacing(6)

        if installation.install_path:
            install_path = QtGui.QLabel(
                "Install: {0}".format(installation.install_path)
            )
            install_path.setWordWrap(True)
            layout.addWidget(install_path)

        if installation.user_config_path:
            user_path = QtGui.QLabel(
                "User config: {0}".format(installation.user_config_path)
            )
            user_path.setWordWrap(True)
            layout.addWidget(user_path)

        status = self.manager.status(installation)
        status_label = QtGui.QLabel(
            "Integration: {0}".format(status.state)
        )
        status_label.setWordWrap(True)
        layout.addWidget(status_label)

        if status.message:
            detail_label = QtGui.QLabel(status.message)
            detail_label.setWordWrap(True)
            layout.addWidget(detail_label)

        row = {
            "installation": installation,
            "status_label": status_label,
        }
        self.rows[installation.key] = row

        if not adapter.integration_available:
            return card

        options = self._default_options(installation)
        component_status = QtGui.QLabel(
            "Loader: {0}    Shelf: {1}    Main Menu: {2}".format(
                "OK" if status.loader else "Missing",
                (
                    "OK" if status.shelf else "Missing"
                ) if options["shelf"] else "Disabled",
                (
                    "Registered" if status.main_menu else "Missing"
                ) if options["main_menu"] else "Disabled"
            )
        )
        component_status.setWordWrap(True)
        layout.addWidget(component_status)

        shelf = QtGui.QCheckBox("Add to Shelf")
        shelf.setChecked(options["shelf"])
        menu = QtGui.QCheckBox("Add to Main Menu")
        menu.setChecked(options["main_menu"])
        auto_open = QtGui.QCheckBox("Open ScriptToolbox on Maya startup")
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
        primary = QtGui.QPushButton(
            "Install"
            if status.state == STATUS_NOT_INSTALLED
            else "Apply Changes"
        )
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
        return card

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
