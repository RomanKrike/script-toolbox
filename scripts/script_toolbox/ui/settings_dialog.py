# -*- coding: utf-8 -*-
from __future__ import print_function

from .. import telemetry
from ..compat import QtCore
from ..compat import QtGui
from ..constants import BUILD_CHANNEL
from ..constants import BUILD_COMMIT
from ..constants import BUILD_NUMBER
from ..constants import DISPLAY_NAME
from ..constants import GITHUB_REPOSITORY
from ..constants import PLUGIN_VERSION
from ..core import http_transport
from ..core import network_proxy
from ..core.preferences import UPDATE_CHANNEL_DEVELOPMENT
from ..core.preferences import UPDATE_CHANNEL_STABLE
from ..core.preferences import get_telemetry_consent
from ..core.preferences import get_update_channel
from ..pycompat import text_type


_CONSENT_PROMPT_SHOWN = False

_CHANNELS = (
    ("Stable", UPDATE_CHANNEL_STABLE),
    ("Development", UPDATE_CHANNEL_DEVELOPMENT),
)

_TELEMETRY_CHOICES = (
    ("Ask me next time", None),
    ("Enabled", True),
    ("Disabled", False),
)

_PROXY_MODES = (
    ("No proxy", network_proxy.PROXY_MODE_NONE),
    ("System proxy", network_proxy.PROXY_MODE_SYSTEM),
    ("Manual proxy", network_proxy.PROXY_MODE_MANUAL),
)

_PROXY_TYPES = (
    ("HTTP", network_proxy.PROXY_TYPE_HTTP),
    ("HTTPS", network_proxy.PROXY_TYPE_HTTPS),
    ("SOCKS5", network_proxy.PROXY_TYPE_SOCKS5),
)

_GITHUB_URL = "https://github.com/RomanKrike/script-toolbox"
_DOCS_URL = "https://romankrike.github.io/script-toolbox/"
_ICONIFY_URL = "https://iconify.design/"
_SOLAR_LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"


class TelemetryConsentDialog(QtGui.QDialog):
    """Explicit first-run opt-in dialog for pseudonymous product telemetry."""

    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)

        self.setWindowTitle("Usage Statistics")
        self.setModal(True)
        self.setMinimumWidth(440)

        root = QtGui.QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        title = QtGui.QLabel("Help improve Script Toolbox")
        title_font = title.font()
        title_font.setBold(True)
        title_font.setPointSize(title_font.pointSize() + 1)
        title.setFont(title_font)
        root.addWidget(title)

        intro = QtGui.QLabel(
            "Script Toolbox can send pseudonymous usage statistics so we can "
            "understand which features are useful and which versions are "
            "actively used."
        )
        intro.setWordWrap(True)
        root.addWidget(intro)

        collected = QtGui.QLabel(
            "Collected: Script Toolbox version, build channel, host "
            "application/version, operating system, feature event names, and "
            "a random Script Toolbox installation identifier reused across "
            "application sessions."
        )
        collected.setWordWrap(True)
        root.addWidget(collected)

        excluded = QtGui.QLabel(
            "Not collected: scene contents, filenames, paths, object names, "
            "scripts, usernames, hostnames, Autodesk account data, hardware "
            "identifiers, or identifiers derived from your device or account."
        )
        excluded.setWordWrap(True)
        root.addWidget(excluded)

        later = QtGui.QLabel(
            "You can change this later in Script Toolbox Settings > Privacy."
        )
        later.setWordWrap(True)
        root.addWidget(later)

        buttons = QtGui.QHBoxLayout()
        buttons.addStretch(1)

        decline_button = QtGui.QPushButton("Don't Send")
        enable_button = QtGui.QPushButton("Enable")
        enable_button.setDefault(True)

        decline_button.clicked.connect(self._decline)
        enable_button.clicked.connect(self._enable)

        buttons.addWidget(decline_button)
        buttons.addWidget(enable_button)
        root.addLayout(buttons)

    def _enable(self):
        telemetry.apply_telemetry_consent(True)
        self.accept()

    def _decline(self):
        telemetry.apply_telemetry_consent(False)
        self.reject()


class NetworkConnectionTest(QtCore.QThread):
    """Run the shared updater transport without blocking the settings UI."""

    completed = QtCore.Signal(bool, object)

    def __init__(self, proxy_config, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.proxy_config = proxy_config

    def run(self):
        url = "https://api.github.com/repos/{0}/releases/latest".format(
            GITHUB_REPOSITORY
        )
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "Script-Toolbox-Proxy-Test/{0}".format(
                PLUGIN_VERSION
            ),
        }
        try:
            http_transport.request_bytes(
                url,
                headers=headers,
                timeout=8,
                proxy_config=self.proxy_config
            )
        except Exception as exc:
            self.completed.emit(
                False,
                http_transport.user_error_message(
                    exc,
                    proxy_config=self.proxy_config
                )
            )
            return

        self.completed.emit(True, "Connected successfully.")


class SettingsDialog(QtGui.QDialog):
    """Application settings with category navigation and stacked pages."""

    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)

        self.setWindowTitle("Script Toolbox Settings")
        self.setModal(True)
        self.setMinimumSize(680, 500)
        self._network_test = None

        root = QtGui.QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        content_layout = QtGui.QHBoxLayout()
        content_layout.setSpacing(16)
        root.addLayout(content_layout, 1)

        self.category_list = QtGui.QListWidget()
        self.category_list.setObjectName("SettingsCategoryList")
        self.category_list.setFixedWidth(150)
        self.category_list.setSpacing(2)
        self.category_list.setFrameShape(QtGui.QFrame.NoFrame)
        self.category_list.setSelectionMode(
            QtGui.QAbstractItemView.SingleSelection
        )
        content_layout.addWidget(self.category_list)

        separator = QtGui.QFrame()
        separator.setObjectName("SettingsSeparator")
        separator.setFrameShape(QtGui.QFrame.VLine)
        separator.setFrameShadow(QtGui.QFrame.Sunken)
        content_layout.addWidget(separator)

        self.pages = QtGui.QStackedWidget()
        self.pages.setObjectName("SettingsPages")
        content_layout.addWidget(self.pages, 1)

        self.update_channel_combo = QtGui.QComboBox()
        for label, channel in _CHANNELS:
            self.update_channel_combo.addItem(label)

        self.telemetry_combo = QtGui.QComboBox()
        for choice_label, consent in _TELEMETRY_CHOICES:
            self.telemetry_combo.addItem(choice_label)

        self.telemetry_status_label = QtGui.QLabel()
        self.telemetry_status_label.setWordWrap(True)

        self._create_network_controls()

        self._add_category("General", self._build_general_page())
        self._add_category("Network", self._build_network_page())
        self._add_category("Privacy", self._build_privacy_page())
        self._add_category("About", self._build_about_page())

        self.category_list.currentRowChanged.connect(
            self.pages.setCurrentIndex
        )
        self.category_list.setCurrentRow(0)

        buttons = QtGui.QHBoxLayout()
        buttons.addStretch(1)

        cancel_button = QtGui.QPushButton("Cancel")
        save_button = QtGui.QPushButton("Save")
        save_button.setDefault(True)

        cancel_button.clicked.connect(self.reject)
        save_button.clicked.connect(self._save)

        buttons.addWidget(cancel_button)
        buttons.addWidget(save_button)
        root.addLayout(buttons)

        self._load_values()

    def _create_network_controls(self):
        self.proxy_mode_combo = QtGui.QComboBox()
        for label, value in _PROXY_MODES:
            self.proxy_mode_combo.addItem(label)

        self.proxy_type_combo = QtGui.QComboBox()
        for label, value in _PROXY_TYPES:
            self.proxy_type_combo.addItem(label)

        self.proxy_host_edit = QtGui.QLineEdit()
        self.proxy_host_edit.setPlaceholderText("proxy.company.local")

        self.proxy_port_edit = QtGui.QLineEdit()
        self.proxy_port_edit.setPlaceholderText("8080")
        try:
            validator = QtGui.QIntValidator(1, 65535, self.proxy_port_edit)
            self.proxy_port_edit.setValidator(validator)
        except Exception:
            pass

        self.proxy_auth_check = QtGui.QCheckBox("Requires authentication")
        self.proxy_username_edit = QtGui.QLineEdit()
        self.proxy_password_edit = QtGui.QLineEdit()
        self.proxy_password_edit.setEchoMode(QtGui.QLineEdit.Password)

        self.proxy_show_password_check = QtGui.QCheckBox("Show password")
        self.proxy_test_button = QtGui.QPushButton("Test connection")
        self.proxy_status_label = QtGui.QLabel("Not tested")
        self.proxy_status_label.setWordWrap(True)

        self.proxy_mode_combo.currentIndexChanged.connect(
            self._update_network_state
        )
        self.proxy_auth_check.toggled.connect(
            self._update_network_state
        )
        self.proxy_show_password_check.toggled.connect(
            self._toggle_password_visibility
        )
        self.proxy_test_button.clicked.connect(
            self._test_connection
        )

    def _add_category(self, label, page):
        self.category_list.addItem(label)
        self.pages.addWidget(page)

    def _build_page_header(self, title_text, description_text):
        header = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        title = QtGui.QLabel(title_text)
        title.setObjectName("SettingsPageTitle")
        title_font = title.font()
        title_font.setBold(True)
        title_font.setPointSize(title_font.pointSize() + 2)
        title.setFont(title_font)
        layout.addWidget(title)

        description = QtGui.QLabel(description_text)
        description.setObjectName("SettingsPageDescription")
        description.setWordWrap(True)
        layout.addWidget(description)
        return header

    def _build_general_page(self):
        page = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(page)
        layout.setContentsMargins(4, 0, 0, 0)
        layout.setSpacing(16)

        layout.addWidget(
            self._build_page_header(
                "General",
                "Application and update preferences for Script Toolbox."
            )
        )

        form = QtGui.QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(10)
        form.addRow("Update channel", self.update_channel_combo)
        layout.addLayout(form)
        layout.addStretch(1)
        return page

    def _build_network_page(self):
        page = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(page)
        layout.setContentsMargins(4, 0, 0, 0)
        layout.setSpacing(14)

        layout.addWidget(
            self._build_page_header(
                "Network",
                "Configure how Script Toolbox connects to update and share services."
            )
        )

        section_title = QtGui.QLabel("Proxy")
        font = section_title.font()
        font.setBold(True)
        section_title.setFont(font)
        layout.addWidget(section_title)

        form = QtGui.QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(9)
        form.addRow("Proxy mode", self.proxy_mode_combo)
        form.addRow("Proxy type", self.proxy_type_combo)
        form.addRow("Host", self.proxy_host_edit)
        form.addRow("Port", self.proxy_port_edit)
        form.addRow("", self.proxy_auth_check)
        form.addRow("Username", self.proxy_username_edit)
        form.addRow("Password", self.proxy_password_edit)
        form.addRow("", self.proxy_show_password_check)
        layout.addLayout(form)

        actions = QtGui.QHBoxLayout()
        actions.addWidget(self.proxy_test_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        layout.addWidget(self.proxy_status_label)

        security_note = QtGui.QLabel(
            "Proxy passwords are never written to settings.json in clear text. "
            "On Windows they are protected with the current user's DPAPI key. "
            "On platforms without a secure built-in backend, the password must "
            "be re-entered after restart."
        )
        security_note.setWordWrap(True)
        layout.addWidget(security_note)
        layout.addStretch(1)
        return page

    def _build_privacy_page(self):
        page = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(page)
        layout.setContentsMargins(4, 0, 0, 0)
        layout.setSpacing(14)

        layout.addWidget(
            self._build_page_header(
                "Privacy",
                "Control optional usage statistics and review what is sent."
            )
        )

        form = QtGui.QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(10)
        form.addRow("Usage statistics", self.telemetry_combo)
        layout.addLayout(form)

        privacy_text = QtGui.QLabel(
            "When enabled, Script Toolbox sends only reviewed technical "
            "metadata, feature event names, and a random installation ID that "
            "is stored locally and reused across sessions. It is not derived "
            "from hardware, account, username, hostname, scene, or project data."
        )
        privacy_text.setWordWrap(True)
        layout.addWidget(privacy_text)

        provider = telemetry.active_provider_name()
        if provider == "none":
            transport_text = (
                "Telemetry transport is not configured in this build. "
                "Your preference is still saved for future official builds."
            )
        else:
            transport_text = "Telemetry transport is available in this build."

        self.telemetry_status_label.setText(transport_text)
        layout.addWidget(self.telemetry_status_label)
        layout.addStretch(1)
        return page

    def _build_about_page(self):
        page = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(page)
        layout.setContentsMargins(4, 0, 0, 0)
        layout.setSpacing(14)

        layout.addWidget(
            self._build_page_header(
                "About",
                "Version, project links, and third-party credits."
            )
        )

        product_name = QtGui.QLabel(DISPLAY_NAME)
        product_font = product_name.font()
        product_font.setBold(True)
        product_font.setPointSize(product_font.pointSize() + 1)
        product_name.setFont(product_font)
        layout.addWidget(product_name)

        version_form = QtGui.QFormLayout()
        version_form.setContentsMargins(0, 0, 0, 0)
        version_form.setSpacing(8)
        version_form.addRow("Version", QtGui.QLabel(PLUGIN_VERSION))

        build_text = BUILD_CHANNEL.title()
        if BUILD_NUMBER:
            build_text += " #{0}".format(BUILD_NUMBER)
        if BUILD_COMMIT:
            build_text += " ({0})".format(BUILD_COMMIT[:8])

        version_form.addRow("Build", QtGui.QLabel(build_text))
        layout.addLayout(version_form)

        links = QtGui.QLabel(
            '<a href="{0}">GitHub repository</a> &nbsp;&middot;&nbsp; '
            '<a href="{1}">Documentation</a>'.format(
                _GITHUB_URL,
                _DOCS_URL
            )
        )
        links.setOpenExternalLinks(True)
        layout.addWidget(links)

        credits_title = QtGui.QLabel("Third-party assets")
        credits_font = credits_title.font()
        credits_font.setBold(True)
        credits_title.setFont(credits_font)
        layout.addWidget(credits_title)

        credits = QtGui.QLabel(
            'Solar Icons by 480 Design<br>'
            'Source: <a href="{0}">Iconify</a><br>'
            'License: <a href="{1}">CC BY 4.0</a>'.format(
                _ICONIFY_URL,
                _SOLAR_LICENSE_URL
            )
        )
        credits.setOpenExternalLinks(True)
        credits.setWordWrap(True)
        layout.addWidget(credits)

        credits_note = QtGui.QLabel(
            "Script Toolbox bundles selected monochrome Solar Linear icons "
            "locally and normalizes their display color for the dark UI. "
            "The full attribution notice is included with the icon resources."
        )
        credits_note.setWordWrap(True)
        layout.addWidget(credits_note)
        layout.addStretch(1)
        return page

    @staticmethod
    def _combo_value(combo, entries):
        index = combo.currentIndex()
        if index < 0 or index >= len(entries):
            index = 0
        return entries[index][1]

    @staticmethod
    def _set_combo_value(combo, entries, value):
        for index, entry in enumerate(entries):
            if entry[1] == value:
                combo.setCurrentIndex(index)
                return
        combo.setCurrentIndex(0)

    def _load_values(self):
        channel = get_update_channel()
        self._set_combo_value(
            self.update_channel_combo,
            _CHANNELS,
            channel
        )

        consent = get_telemetry_consent()
        self._set_combo_value(
            self.telemetry_combo,
            _TELEMETRY_CHOICES,
            consent
        )

        config = network_proxy.load_proxy_config()
        self._set_combo_value(
            self.proxy_mode_combo,
            _PROXY_MODES,
            config.mode
        )
        self._set_combo_value(
            self.proxy_type_combo,
            _PROXY_TYPES,
            config.proxy_type
        )
        self.proxy_host_edit.setText(config.host)
        self.proxy_port_edit.setText(
            "" if config.port is None else text_type(config.port)
        )
        self.proxy_auth_check.setChecked(config.requires_auth)
        self.proxy_username_edit.setText(config.username)
        self.proxy_password_edit.setText(config.password)
        self.proxy_status_label.setText("Not tested")
        self._update_network_state()

    def _update_network_state(self, *args):
        manual = (
            self._combo_value(
                self.proxy_mode_combo,
                _PROXY_MODES
            ) == network_proxy.PROXY_MODE_MANUAL
        )
        auth = manual and self.proxy_auth_check.isChecked()

        self.proxy_type_combo.setEnabled(manual)
        self.proxy_host_edit.setEnabled(manual)
        self.proxy_port_edit.setEnabled(manual)
        self.proxy_auth_check.setEnabled(manual)
        self.proxy_username_edit.setEnabled(auth)
        self.proxy_password_edit.setEnabled(auth)
        self.proxy_show_password_check.setEnabled(auth)

    def _toggle_password_visibility(self, checked):
        mode = (
            QtGui.QLineEdit.Normal
            if checked
            else QtGui.QLineEdit.Password
        )
        self.proxy_password_edit.setEchoMode(mode)

    def _proxy_config_from_ui(self):
        port_text = text_type(self.proxy_port_edit.text()).strip()
        port = None
        if port_text:
            try:
                port = int(port_text)
            except (TypeError, ValueError):
                port = port_text

        config = network_proxy.ProxyConfig(
            mode=self._combo_value(
                self.proxy_mode_combo,
                _PROXY_MODES
            ),
            proxy_type=self._combo_value(
                self.proxy_type_combo,
                _PROXY_TYPES
            ),
            host=text_type(self.proxy_host_edit.text()).strip(),
            port=port,
            requires_auth=self.proxy_auth_check.isChecked(),
            username=text_type(self.proxy_username_edit.text()),
            password=text_type(self.proxy_password_edit.text())
        )
        config.validate()
        return config

    def _test_connection(self):
        try:
            config = self._proxy_config_from_ui()
        except network_proxy.ProxyConfigError as exc:
            self.proxy_status_label.setText(text_type(exc))
            return

        if self._network_test is not None:
            try:
                if self._network_test.isRunning():
                    return
            except Exception:
                pass

        self.proxy_test_button.setEnabled(False)
        self.proxy_status_label.setText("Testing...")

        self._network_test = NetworkConnectionTest(
            config,
            parent=self
        )
        self._network_test.completed.connect(
            self._network_test_finished
        )
        self._network_test.start()

    def _network_test_finished(self, success, message):
        self.proxy_test_button.setEnabled(True)
        self.proxy_status_label.setText(text_type(message))

    def _save(self):
        try:
            proxy_config = self._proxy_config_from_ui()
        except network_proxy.ProxyConfigError as exc:
            self.category_list.setCurrentRow(1)
            self.proxy_status_label.setText(text_type(exc))
            return

        password_persisted = network_proxy.save_proxy_config(
            proxy_config
        )
        if (
            proxy_config.requires_auth and
            proxy_config.password and
            not password_persisted
        ):
            self.category_list.setCurrentRow(1)
            self.proxy_status_label.setText(
                "Settings saved, but this platform has no built-in secure "
                "credential backend. Re-enter the proxy password after restart."
            )

        channel = self._combo_value(
            self.update_channel_combo,
            _CHANNELS
        )
        consent = self._combo_value(
            self.telemetry_combo,
            _TELEMETRY_CHOICES
        )

        parent = self.parent()
        current_channel = get_update_channel()
        if channel != current_channel:
            if parent is not None and hasattr(parent, "set_update_channel"):
                parent.set_update_channel(channel)
            else:
                from ..core.preferences import set_update_channel
                set_update_channel(channel)

        if consent is not get_telemetry_consent():
            telemetry.apply_telemetry_consent(consent)

        self.accept()


def prompt_telemetry_consent(parent=None):
    """Show the opt-in prompt once per process while consent is undecided."""
    global _CONSENT_PROMPT_SHOWN

    if _CONSENT_PROMPT_SHOWN:
        return get_telemetry_consent()

    if get_telemetry_consent() is not None:
        return get_telemetry_consent()

    if telemetry.active_provider_name() == "none":
        return None

    _CONSENT_PROMPT_SHOWN = True
    dialog = TelemetryConsentDialog(parent=parent)
    dialog.exec_()
    return get_telemetry_consent()


def show_settings_dialog(parent=None):
    dialog = SettingsDialog(parent=parent)
    dialog.exec_()
    return dialog


__all__ = [
    "NetworkConnectionTest",
    "SettingsDialog",
    "TelemetryConsentDialog",
    "prompt_telemetry_consent",
    "show_settings_dialog",
]
