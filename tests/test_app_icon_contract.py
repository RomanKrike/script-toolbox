# -*- coding: utf-8 -*-

import os
import importlib.util
import struct
import sys
import types

import pytest


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


@pytest.mark.parametrize("filename", [
    "logo_sbt.ico",
    "logo_sbt_monochrome.ico",
])
def test_brand_icons_contain_complete_windows_size_set(filename):
    path = os.path.join(
        ROOT, "scripts", "script_toolbox", "resources", filename
    )
    with open(path, "rb") as handle:
        data = handle.read()
    reserved, icon_type, count = struct.unpack_from("<HHH", data)
    assert (reserved, icon_type) == (0, 1)
    sizes = set()
    for index in range(count):
        width, height, colors, unused, planes, bits, length, offset = (
            struct.unpack_from("<BBBBHHII", data, 6 + index * 16)
        )
        size = (width or 256, height or 256)
        sizes.add(size)
        assert unused == 0
        assert planes == 1
        assert bits == 32
        assert length > 0
        assert offset >= 6 + count * 16
        assert offset + length <= len(data)
        if size == (256, 256):
            assert data[offset:offset + 8] == b"\x89PNG\r\n\x1a\n"
        else:
            assert struct.unpack_from("<I", data, offset)[0] == 40
    assert sizes == {
        (size, size) for size in (16, 20, 24, 32, 40, 48, 64, 96, 128, 256)
    }


def test_color_and_monochrome_window_icons_are_cached_separately(monkeypatch):
    class FakeIcon(object):
        def __init__(self, path):
            self.path = path

        def isNull(self):
            return False

    compat = types.ModuleType("_branding_test.compat")
    compat.QtGui = types.SimpleNamespace(QIcon=FakeIcon)
    monkeypatch.setitem(sys.modules, "_branding_test.compat", compat)
    spec = importlib.util.spec_from_file_location(
        "_branding_test.style.app_icon",
        os.path.join(ROOT, "scripts", "script_toolbox", "style", "app_icon.py")
    )
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    color = helper.application_icon()
    monochrome = helper.application_icon(monochrome=True)
    assert color is helper.application_icon()
    assert monochrome is helper.application_icon(monochrome=True)
    assert color is not monochrome
    assert os.path.basename(color.path) == "logo_sbt.ico"
    assert os.path.basename(monochrome.path) == "logo_sbt_monochrome.ico"
    assert os.path.isfile(color.path)
    assert os.path.isfile(monochrome.path)
    applied = []
    widget = types.SimpleNamespace(setWindowIcon=applied.append)
    helper.apply_window_icon(widget, monochrome=True)
    assert applied == [monochrome]


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
    metadata_builder = _read(
        "tools/build_windows_resources.py"
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

    assert '"ProductName", "Script Toolbox' in metadata_builder
    assert '"FileDescription", "Script Toolbox' in metadata_builder
    assert '"InternalName", "ScriptToolbox' in metadata_builder
    assert '"OriginalFilename", "ScriptToolbox.exe' in metadata_builder
    assert "CompanyName" not in metadata_builder
    assert "BlinPi" not in metadata_builder

    for workflow in (
        dev_workflow,
        standalone_workflow,
    ):
        assert "tools/build_windows_resources.py" in workflow
        assert "tools/embed_windows_icon.py" in workflow
        assert "scripts/script_toolbox/resources/logo_sbt.ico" in workflow
        assert "ScriptToolbox.rc" in workflow
        assert "ScriptToolbox.res" in workflow
        assert "rc /nologo" in workflow
        assert 'ProductName = "Script Toolbox"' in workflow
        assert 'OriginalFilename = "ScriptToolbox.exe"' in workflow
