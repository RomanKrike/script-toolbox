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
    assert '"Open ScriptToolbox on Maya startup"' in source
    assert '"Repair"' in source
    assert '"Uninstall"' in source
    assert '"Install to all detected Maya versions"' in source
