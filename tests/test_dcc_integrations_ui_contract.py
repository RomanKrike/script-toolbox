# -*- coding: utf-8 -*-

import os


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


def _read(relative_path):
    path = os.path.join(ROOT, *relative_path.split("/"))
    with open(path, "r") as handle:
        return handle.read()


def test_settings_dialog_exposes_dcc_integrations_page():
    source = _read("scripts/script_toolbox/ui/settings_dialog.py")
    assert "DccIntegrationsPage" in source
    assert 'self._add_category("DCC Integrations"' in source


def test_dcc_integration_ui_exposes_required_maya_actions():
    source = _read("scripts/script_toolbox/ui/dcc_integrations.py")
    assert '"Scan DCCs"' in source
    assert '"Add to Shelf"' in source
    assert '"Add to Main Menu"' in source
    assert '"Open on startup"' in source
    assert '"Update"' in source
    assert '"Repair"' in source
    assert '"Uninstall"' in source
    assert '"Install to all"' in source


def test_dcc_page_uses_shared_settings_style_primitives_and_metrics():
    source = _read("scripts/script_toolbox/ui/dcc_integrations.py")
    shared = _read("scripts/script_toolbox/ui/settings_components.py")
    stylesheet = _read("scripts/script_toolbox/style/stylesheet.py")
    metrics = _read("scripts/script_toolbox/style/metrics.py")

    assert "from ..style import metrics" in source
    assert "build_page_header" in source
    assert "CollapsibleSection" in source
    assert "configure_settings_scroll_area" in source
    assert "metrics.SETTINGS_PAGE_MARGINS" in source
    assert "metrics.SETTINGS_PAGE_SPACING" in source
    assert "metrics.SETTINGS_SECTION_SPACING" in source
    assert "metrics.SETTINGS_ACTION_SPACING" in source
    assert "QtGui.QGroupBox(" not in source
    assert "build_simple_section" not in source
    assert "setContentsMargins(4, 0, 0, 0)" not in source
    assert "setSpacing(12)" not in source

    assert "from ..style import metrics" in shared
    assert "from ..style import palette" in shared
    assert 'section.setObjectName("SimpleSectionGroupBox")' in shared
    assert 'content.setObjectName("RuntimeFolderContent")' in shared
    assert 'scroll.setObjectName("SettingsScroll")' in shared
    assert 'viewport.setObjectName("SettingsScrollViewport")' in shared
    assert "QtGui.QColor(palette.CONTENT_BG)" in shared
    assert "QtGui.QColor(palette.TEXT_PRIMARY)" in shared

    assert "SETTINGS_PAGE_MARGINS" in metrics
    assert "SETTINGS_PAGE_SPACING" in metrics
    assert "SETTINGS_SECTION_SPACING" in metrics
    assert "SETTINGS_ACTION_SPACING" in metrics
    assert "QScrollArea#SettingsScroll" in stylesheet
    assert "QWidget#SettingsScrollViewport" in stylesheet
    assert "background-color: %(CONTENT_BG)s;" in stylesheet
    assert "color: %(TEXT_MUTED)s;" in stylesheet
    assert "color: %(TEXT_SUBTLE)s;" in stylesheet


def test_dcc_page_uses_nested_collapsible_sections_for_compact_layout():
    source = _read("scripts/script_toolbox/ui/dcc_integrations.py")

    assert "from .collapsible_folder import CollapsibleSection" in source
    assert "def _build_adapter_section(self, adapter):" in source
    assert "def _build_installation_section(self, adapter, installation, parent):" in source
    assert source.count("CollapsibleSection(") >= 2
    assert "nested=False" in source
    assert "nested=True" in source
    assert "collapsed=self._collapsed_value(key, True)" in source
    assert 'adapter.key != "maya" or not installations' in source
    assert "self._collapsed_state = {}" in source
    assert "section.collapsedChanged.connect(" in source


def test_dcc_page_keeps_install_all_inside_maya_section():
    source = _read("scripts/script_toolbox/ui/dcc_integrations.py")

    assert "def _add_install_all_row(self, layout, parent):" in source
    assert '"All versions:"' in source
    assert '"Shelf"' in source
    assert '"Main Menu"' in source
    assert '"Install to all"' in source
    assert "_build_install_all_section" not in source


def test_dcc_headers_summarize_detection_and_version_status():
    source = _read("scripts/script_toolbox/ui/dcc_integrations.py")

    assert "def _adapter_title(self, adapter, installations):" in source
    assert '"Not detected"' in source
    assert '" | Detection only"' in source
    assert 'title="{0}  |  {1}".format(' in source
    assert "status.state" in source
