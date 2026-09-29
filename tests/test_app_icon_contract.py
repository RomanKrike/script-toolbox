# -*- coding: utf-8 -*-

import os


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


def test_application_icon_resource_is_valid_ico():
    path = os.path.join(
        ROOT,
        "scripts",
        "script_toolbox",
        "resources",
        "logo_sbt.ico"
    )

    assert os.path.isfile(path)

    with open(path, "rb") as handle:
        header = handle.read(6)

    assert header[:4] == b"\x00\x00\x01\x00"
    assert header[4:6] != b"\x00\x00"


def test_shared_windows_apply_application_icon():
    helper = _read(
        "scripts/script_toolbox/style/app_icon.py"
    )
    main_window = _read(
        "scripts/script_toolbox/ui/main_window.py"
    )
    editor = _read(
        "scripts/script_toolbox/ui/interface_editor.py"
    )
    settings = _read(
        "scripts/script_toolbox/ui/settings_dialog.py"
    )

    assert '"resources"' in helper
    assert '"logo_sbt.ico"' in helper
    assert "QtGui.QIcon(" in helper
    assert "def apply_window_icon" in helper

    assert "apply_window_icon(" in main_window
    assert "self.logo_label" not in main_window
    assert '"ToolboxLogo"' not in main_window
    assert "apply_window_icon(" in editor
    assert settings.count("apply_window_icon(") >= 2


def test_standalone_application_sets_global_icon_without_touching_dcc_hosts():
    source = _read(
        "scripts/script_toolbox/standalone.py"
    )

    assert '"setWindowIcon"' in source
    assert "from .style import application_icon" in source
    assert "set_window_icon(" in source


def test_windows_launcher_embeds_logo_resource():
    embedder = _read(
        "tools/embed_windows_icon.py"
    )
    dev_workflow = _read(
        ".github/workflows/dev-build.yml"
    )
    standalone_workflow = _read(
        ".github/workflows/standalone-build.yml"
    )

    assert "BeginUpdateResourceW" in embedder
    assert "UpdateResourceW" in embedder
    assert "EndUpdateResourceW" in embedder
    assert "RT_ICON = 3" in embedder
    assert "RT_GROUP_ICON = 14" in embedder
    assert "def parse_ico(" in embedder
    assert "def build_group_icon(" in embedder
    assert "def verify_icon_resource(" in embedder

    for workflow in (
        dev_workflow,
        standalone_workflow,
    ):
        assert "tools/embed_windows_icon.py" in workflow
        assert "scripts/script_toolbox/resources/logo_sbt.ico" in workflow
        assert "rc /nologo" not in workflow
        assert "launcher.res" not in workflow
