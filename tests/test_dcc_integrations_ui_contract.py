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


def test_dcc_integration_ui_exposes_required_actions():
    source = _read("scripts/script_toolbox/ui/dcc_integrations.py")
    base = _read("scripts/script_toolbox/integrations/base.py")
    assert '"Scan DCCs"' in source
    assert '"Update"' in source
    assert '"Repair"' in source
    assert '"Uninstall"' in source
    assert '"Install to all"' in source
    assert '"Add profile path..."' in source
    assert '"Profile locations  |  {0}"' in source
    assert '"Add to Shelf"' in base
    assert '"Add to Main Menu"' in base
    assert '"Open on startup"' in base


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
    assert 'adapter.key != "maya"' in source
    assert "self._collapsed_state = {}" in source
    assert "section.collapsedChanged.connect(" in source


def test_dcc_page_keeps_install_all_inside_maya_section():
    source = _read("scripts/script_toolbox/ui/dcc_integrations.py")

    assert "def _add_install_all_row(self, layout, parent):" in source
    assert '"All profiles:"' in source
    assert '"Shelf"' in source
    assert '"Main Menu"' in source
    assert '"Install to all"' in source
    assert "_build_install_all_section" not in source


def test_dcc_headers_summarize_detection_and_version_status():
    source = _read("scripts/script_toolbox/ui/dcc_integrations.py")

    assert "def _adapter_title(self, adapter, installations):" in source
    assert '"Not detected"' in source
    assert '" | Detection only"' in source
    assert 'title="{0} - {1}  |  {2}".format(' in source
    assert "status.state" in source


def test_dcc_page_exposes_generic_custom_profile_root_controls():
    source = _read("scripts/script_toolbox/ui/dcc_integrations.py")
    manager = _read("scripts/script_toolbox/integrations/manager.py")
    maya = _read("scripts/script_toolbox/integrations/maya.py")
    houdini = _read("scripts/script_toolbox/integrations/houdini.py")
    nuke = _read("scripts/script_toolbox/integrations/nuke.py")

    assert "def _add_profile_locations(" in source
    assert "def _add_profile_path(" in source
    assert "def _remove_profile_path(" in source
    assert "def _supports_profile_locations(adapter):" in source
    assert "QtGui.QFileDialog.getExistingDirectory(" in source
    assert "QtGui.QInputDialog.getText(" in source
    assert 'self.manager.add_profile_root(' in source
    assert 'self.manager.remove_profile_root(' in source
    assert "def add_profile_root(self, dcc, profile_path, label=" in manager
    assert "def remove_profile_root(self, dcc, profile_id):" in manager

    for adapter_source in (maya, houdini, nuke):
        assert "def profile_roots(self):" in adapter_source
        assert "def add_profile_root(self, profile_path, label=" in adapter_source
        assert "def remove_profile_root(self, profile_id):" in adapter_source


def test_dcc_version_headers_include_profile_identity():
    source = _read("scripts/script_toolbox/ui/dcc_integrations.py")

    assert "installation.profile_label" in source
    assert "installation.key" in source
    assert "profile_id=installation.profile_id" in source


def test_dcc_ui_builds_host_specific_integration_options():
    source = _read("scripts/script_toolbox/ui/dcc_integrations.py")
    houdini = _read("scripts/script_toolbox/integrations/houdini.py")
    nuke = _read("scripts/script_toolbox/integrations/nuke.py")

    assert "adapter.option_definitions()" in source
    assert "adapter.component_status_text(" in source
    assert '"Add Houdini Shelf"' in houdini
    assert '"Add to Main Menu"' in nuke
    assert '"Register Dock Panel"' in nuke
    assert '"Open on startup"' in houdini
    assert '"Open on startup"' in nuke


def test_houdini_and_nuke_are_managed_integrations_not_detection_only():
    houdini = _read("scripts/script_toolbox/integrations/houdini.py")
    nuke = _read("scripts/script_toolbox/integrations/nuke.py")

    assert "integration_available = True" in houdini
    assert "supported = True" in houdini
    assert "def install(self, installation, options=None):" in houdini
    assert "def repair(self, installation):" in houdini
    assert "def uninstall(self, installation):" in houdini

    assert "integration_available = True" in nuke
    assert "supported = True" in nuke
    assert "def install(self, installation, options=None):" in nuke
    assert "def repair(self, installation):" in nuke
    assert "def uninstall(self, installation):" in nuke


def test_houdini_and_nuke_custom_profiles_are_profile_aware_at_runtime():
    houdini = _read("scripts/script_toolbox/integrations/houdini.py")
    nuke = _read("scripts/script_toolbox/integrations/nuke.py")
    houdini_runtime = _read("scripts/script_toolbox/houdini_integration.py")
    nuke_runtime = _read("scripts/script_toolbox/nuke_integration.py")

    assert "profile_id=installation.profile_id" in houdini
    assert "profile_id=installation.profile_id" in nuke
    assert "def apply_current_integration(profile_id=None):" in houdini_runtime
    assert "def apply_current_integration(profile_id=None):" in nuke_runtime
    assert "profile_id=profile_id" in houdini_runtime
    assert "profile_id=profile_id" in nuke_runtime
