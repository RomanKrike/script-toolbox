# -*- coding: utf-8 -*-
from __future__ import print_function

from .. import telemetry
from ..compat import QtGui
from ..constants import BUILD_CHANNEL
from ..constants import BUILD_COMMIT
from ..constants import BUILD_NUMBER
from ..constants import DISPLAY_NAME
from ..constants import PLUGIN_VERSION
from ..core.preferences import UPDATE_CHANNEL_DEVELOPMENT
from ..core.preferences import UPDATE_CHANNEL_STABLE
from ..core.preferences import get_telemetry_consent
from ..core.preferences import get_update_channel


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


class SettingsDialog(QtGui.QDialog):
    """Application settings with category navigation and stacked pages."""

    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)

        self.setWindowTitle("Script Toolbox Settings")
        self.setModal(True)
        self.setMinimumSize(640, 420)

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

        self._add_category(
            "General",
            self._build_general_page()
        )
        self._add_category(
            "Privacy",
            self._build_privacy_page()
        )
        self._add_category(
            "About",
            self._build_about_page()
        )

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
        form.addRow(
            "Update channel",
            self.update_channel_combo
        )
        layout.addLayout(form)
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
        form.addRow(
            "Usage statistics",
            self.telemetry_combo
        )
        layout.addLayout(form)

        privacy_text = QtGui.QLabel(
            "When enabled, Script Toolbox sends only reviewed technical "
            "metadata, feature event names, and a random installation ID that "
            "is stored locally and reused across sessions. It is not derived "
            "from hardware, account, username, hostname, scene, or project "
            "data."
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
        version_form.addRow(
            "Version",
            QtGui.QLabel(PLUGIN_VERSION)
        )

        build_text = BUILD_CHANNEL.title()
        if BUILD_NUMBER:
            build_text += " #{0}".format(BUILD_NUMBER)
        if BUILD_COMMIT:
            build_text += " ({0})".format(BUILD_COMMIT[:8])

        version_form.addRow(
            "Build",
            QtGui.QLabel(build_text)
        )
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

    def _load_values(self):
        channel = get_update_channel()
        channel_index = 0
        for index, entry in enumerate(_CHANNELS):
            if entry[1] == channel:
                channel_index = index
                break
        self.update_channel_combo.setCurrentIndex(channel_index)

        consent = get_telemetry_consent()
        consent_index = 0
        for index, entry in enumerate(_TELEMETRY_CHOICES):
            if entry[1] is consent:
                consent_index = index
                break
        self.telemetry_combo.setCurrentIndex(consent_index)

    def _save(self):
        channel = _CHANNELS[
            self.update_channel_combo.currentIndex()
        ][1]
        consent = _TELEMETRY_CHOICES[
            self.telemetry_combo.currentIndex()
        ][1]

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
    "SettingsDialog",
    "TelemetryConsentDialog",
    "prompt_telemetry_consent",
    "show_settings_dialog",
]
