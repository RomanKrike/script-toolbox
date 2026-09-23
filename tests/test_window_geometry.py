# -*- coding: utf-8 -*-

import os

from script_toolbox.core.preferences import load_preferences
from script_toolbox.core.preferences import save_preferences
from script_toolbox.core.window_geometry import get_window_geometry
from script_toolbox.core.window_geometry import normalize_window_geometry
from script_toolbox.core.window_geometry import set_window_geometry


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


def _read(relative_path):
    path = os.path.join(
        ROOT,
        *relative_path.split("/")
    )
    with open(path, "r") as handle:
        return handle.read()


def test_window_geometry_accepts_negative_multimonitor_coordinates():
    value = {
        "x": -1840,
        "y": 120,
        "width": 520,
        "height": 760,
    }

    assert normalize_window_geometry(value) == value


def test_window_geometry_rejects_invalid_or_unsafe_sizes():
    assert normalize_window_geometry(None) is None
    assert normalize_window_geometry({
        "x": 10,
        "y": 10,
        "width": 100,
        "height": 700,
    }) is None
    assert normalize_window_geometry({
        "x": 10,
        "y": 10,
        "width": 420,
        "height": 100001,
    }) is None
    assert normalize_window_geometry({
        "x": 10,
        "y": 10,
        "width": 420,
    }) is None


def test_window_geometry_persists_without_overwriting_other_preferences(tmp_path):
    path = str(
        tmp_path / "settings.json"
    )
    save_preferences(
        {
            "update_channel": "development",
        },
        path=path
    )

    geometry = {
        "x": -1200,
        "y": 45,
        "width": 640,
        "height": 800,
    }

    assert set_window_geometry(
        geometry,
        path=path
    ) == geometry
    assert get_window_geometry(
        path=path
    ) == geometry
    assert load_preferences(
        path=path
    )["update_channel"] == "development"


def test_floating_toolbox_geometry_is_screen_safe_and_debounced():
    source = _read(
        "scripts/script_toolbox/ui/window_geometry.py"
    )

    assert "desktop.availableGeometry(" in source
    assert "desktop.screenNumber(" in source
    assert "ensure_window_visible(" in source
    assert "restore_window_geometry(" in source
    assert "QtCore.QEvent.Move" in source
    assert "QtCore.QEvent.Resize" in source
    assert "QtCore.QEvent.Close" in source
    assert "POST_SHOW_VALIDATE_MS" in source
    assert "save_timer.setSingleShot(" in source


def test_normal_show_installs_geometry_recovery_but_dock_registration_does_not():
    bootstrap = _read(
        "scripts/script_toolbox/bootstrap.py"
    )
    nuke_integration = _read(
        "scripts/script_toolbox/nuke_integration.py"
    )

    assert "install_window_geometry_persistence" in bootstrap
    assert "install_window_geometry_persistence" not in nuke_integration
