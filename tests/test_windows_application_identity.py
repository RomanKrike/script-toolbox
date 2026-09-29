# -*- coding: utf-8 -*-

import os

from tools.build_windows_resources import render_version_resource
from tools.build_windows_resources import windows_version_tuple


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


def test_windows_app_user_model_id_is_stable_and_applied_before_qapplication():
    identity = _read(
        "scripts/script_toolbox/windows_identity.py"
    )
    standalone = _read(
        "scripts/script_toolbox/standalone.py"
    )
    launcher = _read(
        "standalone/launcher.c"
    )

    assert 'APP_USER_MODEL_ID = "ScriptToolbox.App"' in identity
    assert "SetCurrentProcessExplicitAppUserModelID" in identity
    assert "SetCurrentProcessExplicitAppUserModelID" in launcher
    assert 'L"ScriptToolbox.App"' in launcher

    apply_index = standalone.index(
        "apply_windows_app_user_model_id()"
    )
    qapplication_index = standalone.index(
        "application_class.instance()"
    )
    assert apply_index < qapplication_index


def test_native_launcher_hosts_python_in_process_instead_of_spawning_pythonw():
    launcher = _read(
        "standalone/launcher.c"
    )

    assert "CreateProcessW(" not in launcher
    assert "pythonw.exe" not in launcher
    assert "LoadLibraryExW(" in launcher
    assert 'GetProcAddress(python_module, "Py_Main")' in launcher
    assert "python3*.dll" in launcher


def test_windows_version_resource_metadata_contract():
    assert windows_version_tuple("1.5.2") == (1, 5, 2, 0)
    assert windows_version_tuple("1.5.2-dev.47") == (1, 5, 2, 47)

    resource = render_version_resource(
        "1.5.2-dev.47"
    )

    assert "FILEVERSION 1,5,2,47" in resource
    assert 'VALUE "ProductName", "Script Toolbox\\0"' in resource
    assert 'VALUE "FileDescription", "Script Toolbox\\0"' in resource
    assert 'VALUE "InternalName", "ScriptToolbox\\0"' in resource
    assert 'VALUE "OriginalFilename", "ScriptToolbox.exe\\0"' in resource
    assert "CompanyName" not in resource
    assert "BlinPi" not in resource
