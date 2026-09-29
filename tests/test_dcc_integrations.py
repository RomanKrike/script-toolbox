# -*- coding: utf-8 -*-

import os

from script_toolbox.integrations.base import STATUS_INSTALLED
from script_toolbox.integrations.base import STATUS_NOT_INSTALLED
from script_toolbox.integrations.base import STATUS_PARTIAL
from script_toolbox.integrations.base import STATUS_UPDATE_REQUIRED
from script_toolbox.integrations.config import add_profile_root
from script_toolbox.integrations.config import find_profile_id_for_paths
from script_toolbox.integrations.config import get_integration_settings
from script_toolbox.integrations.config import get_profile_roots
from script_toolbox.integrations.config import remove_profile_root
from script_toolbox.integrations.discovery import parse_version
from script_toolbox.integrations.manager import DccIntegrationManager
from script_toolbox.integrations.maya import MayaAdapter
from script_toolbox.integrations.maya import MayaIntegrationError


def _installation(adapter, version):
    for item in adapter.get_installations():
        if item.version == version and item.profile_id == "default":
            return item
    raise AssertionError("Maya {0} was not detected".format(version))


def _profile_installation(adapter, version, label):
    for item in adapter.get_installations():
        if item.version == version and item.profile_label == label:
            return item
    raise AssertionError(
        "Maya {0} profile {1} was not detected".format(
            version,
            label
        )
    )


def test_version_parsing_handles_dcc_folder_names():
    assert parse_version("Maya2026") == "2026"
    assert parse_version("Maya 2015-x64") == "2015"
    assert parse_version("Houdini 21.0.440") == "21.0.440"
    assert parse_version("Nuke15.2v3") == "15.2"


def test_maya_detection_supports_multiple_versions(tmp_path):
    root = tmp_path / "maya"
    (root / "2015-x64").mkdir(parents=True)
    (root / "2026").mkdir()

    adapter = MayaAdapter(
        distribution_path=str(tmp_path / "ScriptToolbox"),
        user_root=str(root),
        program_files=str(tmp_path / "Program Files"),
        registry_reader=lambda: [
            ("2015", str(tmp_path / "Autodesk" / "Maya2015")),
            ("2026", str(tmp_path / "Autodesk" / "Maya2026")),
        ],
        config_path=str(tmp_path / "dcc_integrations.json")
    )

    installations = adapter.get_installations()
    assert [item.version for item in installations] == ["2015", "2026"]
    assert installations[0].user_config_path.endswith("2015-x64")
    assert installations[1].user_config_path.endswith("2026")
    assert all(item.integration_available for item in installations)


def test_maya_install_is_idempotent_and_preserves_user_setup(tmp_path):
    user_root = tmp_path / "maya"
    user_config = user_root / "2026"
    scripts = user_config / "scripts"
    scripts.mkdir(parents=True)
    user_setup = scripts / "userSetup.py"
    user_setup.write_text("print('keep me')\n", encoding="utf-8")

    adapter = MayaAdapter(
        distribution_path=str(tmp_path / "ScriptToolbox"),
        user_root=str(user_root),
        program_files=str(tmp_path / "Program Files"),
        registry_reader=lambda: [("2026", str(tmp_path / "Maya2026"))],
        config_path=str(tmp_path / "dcc_integrations.json")
    )
    installation = _installation(adapter, "2026")

    first = adapter.install(
        installation,
        {"shelf": True, "main_menu": True, "auto_open": False}
    )
    first_user_setup = user_setup.read_text(encoding="utf-8")
    second = adapter.install(
        installation,
        {"shelf": True, "main_menu": True, "auto_open": False}
    )
    second_user_setup = user_setup.read_text(encoding="utf-8")

    assert first.state == STATUS_INSTALLED
    assert second.state == STATUS_INSTALLED
    assert first_user_setup == second_user_setup
    assert "print('keep me')" in second_user_setup
    assert second_user_setup.count("ScriptToolbox DCC Integration >>>") == 1
    assert os.path.isfile(str(user_setup) + ".script_toolbox.bak")

    shelf_path = (
        user_config / "prefs" / "shelves" / "shelf_ScriptToolbox.mel"
    )
    assert shelf_path.is_file()
    assert "ScriptToolboxOpenButton" in shelf_path.read_text(encoding="utf-8")


def test_maya_status_and_repair_detect_missing_shelf(tmp_path):
    user_root = tmp_path / "maya"
    (user_root / "2026").mkdir(parents=True)
    adapter = MayaAdapter(
        distribution_path=str(tmp_path / "ScriptToolbox"),
        user_root=str(user_root),
        registry_reader=lambda: [("2026", str(tmp_path / "Maya2026"))],
        config_path=str(tmp_path / "dcc_integrations.json")
    )
    installation = _installation(adapter, "2026")
    adapter.install(installation)

    shelf_path = (
        user_root / "2026" / "prefs" / "shelves" /
        "shelf_ScriptToolbox.mel"
    )
    shelf_path.unlink()

    assert adapter.status(installation).state == STATUS_PARTIAL
    assert adapter.repair(installation).state == STATUS_INSTALLED
    assert shelf_path.is_file()


def test_maya_uninstall_preserves_foreign_user_setup_content(tmp_path):
    user_root = tmp_path / "maya"
    user_config = user_root / "2026"
    scripts = user_config / "scripts"
    scripts.mkdir(parents=True)
    user_setup = scripts / "userSetup.py"
    user_setup.write_text(
        "import studio_bootstrap\nstudio_bootstrap.start()\n",
        encoding="utf-8"
    )

    config_path = str(tmp_path / "dcc_integrations.json")
    adapter = MayaAdapter(
        distribution_path=str(tmp_path / "ScriptToolbox"),
        user_root=str(user_root),
        registry_reader=lambda: [("2026", str(tmp_path / "Maya2026"))],
        config_path=config_path
    )
    installation = _installation(adapter, "2026")
    adapter.install(installation)
    result = adapter.uninstall(installation)

    assert result.state == STATUS_NOT_INSTALLED
    content = user_setup.read_text(encoding="utf-8")
    assert content == "import studio_bootstrap\nstudio_bootstrap.start()\n"
    assert "ScriptToolbox DCC Integration" not in content
    assert get_integration_settings("maya", "2026", path=config_path) is None
    assert not os.path.exists(adapter._module_path(installation))


def test_maya_versions_keep_independent_options(tmp_path):
    user_root = tmp_path / "maya"
    (user_root / "2015").mkdir(parents=True)
    (user_root / "2026").mkdir()
    config_path = str(tmp_path / "dcc_integrations.json")
    adapter = MayaAdapter(
        distribution_path=str(tmp_path / "ScriptToolbox"),
        user_root=str(user_root),
        registry_reader=lambda: [
            ("2015", str(tmp_path / "Maya2015")),
            ("2026", str(tmp_path / "Maya2026")),
        ],
        config_path=config_path
    )

    maya2015 = _installation(adapter, "2015")
    maya2026 = _installation(adapter, "2026")
    adapter.install(
        maya2015,
        {"shelf": False, "main_menu": True, "auto_open": False}
    )
    adapter.install(
        maya2026,
        {"shelf": True, "main_menu": False, "auto_open": False}
    )

    settings2015 = get_integration_settings("maya", "2015", path=config_path)
    settings2026 = get_integration_settings("maya", "2026", path=config_path)
    assert settings2015["shelf"] is False
    assert settings2015["main_menu"] is True
    assert settings2026["shelf"] is True
    assert settings2026["main_menu"] is False

    module2015 = adapter._module_path(maya2015)
    module2026 = adapter._module_path(maya2026)
    assert os.path.isfile(module2015)
    assert os.path.isfile(module2026)

    adapter.uninstall(maya2015)
    assert not os.path.exists(module2015)
    assert os.path.isfile(module2026)
    assert get_integration_settings("maya", "2026", path=config_path) is not None
    assert adapter.status(maya2026).state == STATUS_INSTALLED


def test_maya_backend_only_does_not_create_startup_or_shelf(tmp_path):
    user_root = tmp_path / "maya"
    (user_root / "2026").mkdir(parents=True)
    adapter = MayaAdapter(
        distribution_path=str(tmp_path / "ScriptToolbox"),
        user_root=str(user_root),
        registry_reader=lambda: [("2026", str(tmp_path / "Maya2026"))],
        config_path=str(tmp_path / "dcc_integrations.json")
    )
    installation = _installation(adapter, "2026")
    result = adapter.install(
        installation,
        {"shelf": False, "main_menu": False, "auto_open": False}
    )

    assert result.state == STATUS_INSTALLED
    assert os.path.isfile(adapter._module_path(installation))
    assert not os.path.exists(adapter._user_setup_path(installation))
    assert not os.path.exists(adapter._shelf_path(installation))


def test_maya_install_refuses_to_overwrite_foreign_shelf(tmp_path):
    user_root = tmp_path / "maya"
    user_config = user_root / "2026"
    shelf_dir = user_config / "prefs" / "shelves"
    shelf_dir.mkdir(parents=True)
    shelf = shelf_dir / "shelf_ScriptToolbox.mel"
    shelf.write_text("// user-owned shelf\n", encoding="utf-8")

    adapter = MayaAdapter(
        distribution_path=str(tmp_path / "ScriptToolbox"),
        user_root=str(user_root),
        registry_reader=lambda: [("2026", str(tmp_path / "Maya2026"))],
        config_path=str(tmp_path / "dcc_integrations.json")
    )
    installation = _installation(adapter, "2026")

    import pytest
    from script_toolbox.integrations.maya import MayaIntegrationError
    with pytest.raises(MayaIntegrationError):
        adapter.install(installation)

    assert shelf.read_text(encoding="utf-8") == "// user-owned shelf\n"


def test_capability_flags_do_not_claim_unimplemented_integrations_are_supported():
    adapters = {
        adapter.key: adapter
        for adapter in DccIntegrationManager().adapters()
    }

    assert adapters["maya"].supported is True
    assert adapters["maya"].integration_available is True
    for key in ("houdini", "nuke", "blender", "3dsmax"):
        assert adapters[key].supported is False
        assert adapters[key].integration_available is False


def test_maya_update_required_is_repaired_by_install(tmp_path):
    user_root = tmp_path / "maya"
    (user_root / "2026").mkdir(parents=True)
    adapter = MayaAdapter(
        distribution_path=str(tmp_path / "ScriptToolbox"),
        user_root=str(user_root),
        registry_reader=lambda: [("2026", str(tmp_path / "Maya2026"))],
        config_path=str(tmp_path / "dcc_integrations.json")
    )
    installation = _installation(adapter, "2026")
    adapter.install(
        installation,
        {"shelf": True, "main_menu": True, "auto_open": False}
    )

    module_path = adapter._module_path(installation)
    with open(module_path, "r") as handle:
        stale = handle.read()
    stale = stale.replace(
        adapter.distribution_path.replace("\\", "/"),
        str(tmp_path / "OldScriptToolbox").replace("\\", "/")
    )
    with open(module_path, "w") as handle:
        handle.write(stale)

    assert adapter.status(installation).state == STATUS_UPDATE_REQUIRED
    result = adapter.install(
        installation,
        {"shelf": True, "main_menu": True, "auto_open": False}
    )
    assert result.state == STATUS_INSTALLED


def test_custom_maya_profile_root_discovers_same_version_independently(tmp_path):
    default_root = tmp_path / "maya"
    custom_root = tmp_path / "parovoz" / "maya" / "rkrikunov"
    (default_root / "2025").mkdir(parents=True)
    (custom_root / "2025").mkdir(parents=True)

    config_path = str(tmp_path / "dcc_integrations.json")
    record = add_profile_root(
        "maya",
        str(custom_root),
        label="Parovoz",
        path=config_path
    )

    adapter = MayaAdapter(
        distribution_path=str(tmp_path / "ScriptToolbox"),
        user_root=str(default_root),
        registry_reader=lambda: [
            ("2025", str(tmp_path / "Autodesk" / "Maya2025"))
        ],
        config_path=config_path
    )

    targets = [
        item for item in adapter.get_installations()
        if item.version == "2025"
    ]
    assert len(targets) == 2
    assert [item.profile_label for item in targets] == [
        "Default",
        "Parovoz",
    ]
    assert targets[0].profile_id == "default"
    assert targets[1].profile_id == record["id"]
    assert targets[0].key != targets[1].key
    assert targets[0].user_config_path.endswith(
        os.path.join("maya", "2025")
    )
    assert targets[1].user_config_path == os.path.normpath(
        str(custom_root / "2025")
    )


def test_custom_maya_profile_root_can_point_to_specific_version(tmp_path):
    default_root = tmp_path / "maya"
    version_profile = tmp_path / "studio" / "maya" / "2025"
    default_root.mkdir(parents=True)
    version_profile.mkdir(parents=True)

    config_path = str(tmp_path / "dcc_integrations.json")
    add_profile_root(
        "maya",
        str(version_profile),
        label="Studio 2025",
        path=config_path
    )

    adapter = MayaAdapter(
        distribution_path=str(tmp_path / "ScriptToolbox"),
        user_root=str(default_root),
        registry_reader=lambda: [
            ("2025", str(tmp_path / "Autodesk" / "Maya2025"))
        ],
        config_path=config_path
    )

    custom = _profile_installation(adapter, "2025", "Studio 2025")
    assert custom.user_config_path == os.path.normpath(
        str(version_profile)
    )
    assert custom.profile_source == "custom"


def test_same_maya_version_profiles_keep_independent_integration_settings(tmp_path):
    default_root = tmp_path / "maya"
    custom_root = tmp_path / "parovoz" / "maya" / "rkrikunov"
    (default_root / "2025").mkdir(parents=True)
    (custom_root / "2025").mkdir(parents=True)
    config_path = str(tmp_path / "dcc_integrations.json")

    add_profile_root(
        "maya",
        str(custom_root),
        label="Parovoz",
        path=config_path
    )
    adapter = MayaAdapter(
        distribution_path=str(tmp_path / "ScriptToolbox"),
        user_root=str(default_root),
        registry_reader=lambda: [
            ("2025", str(tmp_path / "Autodesk" / "Maya2025"))
        ],
        config_path=config_path
    )

    default = _profile_installation(adapter, "2025", "Default")
    parovoz = _profile_installation(adapter, "2025", "Parovoz")

    adapter.install(
        default,
        {"shelf": False, "main_menu": True, "auto_open": False}
    )
    adapter.install(
        parovoz,
        {"shelf": True, "main_menu": False, "auto_open": False}
    )

    default_settings = get_integration_settings(
        "maya",
        "2025",
        path=config_path,
        profile_id=default.profile_id
    )
    parovoz_settings = get_integration_settings(
        "maya",
        "2025",
        path=config_path,
        profile_id=parovoz.profile_id
    )

    assert default_settings["shelf"] is False
    assert default_settings["main_menu"] is True
    assert parovoz_settings["shelf"] is True
    assert parovoz_settings["main_menu"] is False
    assert os.path.isfile(adapter._module_path(default))
    assert os.path.isfile(adapter._module_path(parovoz))


def test_runtime_profile_resolution_matches_custom_maya_app_dir(tmp_path):
    config_path = str(tmp_path / "dcc_integrations.json")
    custom_root = tmp_path / "parovoz" / "preferences" / "maya" / "rkrikunov"
    custom_version = custom_root / "2025"
    custom_version.mkdir(parents=True)

    record = add_profile_root(
        "maya",
        str(custom_root),
        label="Parovoz",
        path=config_path
    )

    resolved = find_profile_id_for_paths(
        "maya",
        [
            str(custom_root),
            str(custom_version),
        ],
        path=config_path
    )
    assert resolved == record["id"]

    assert find_profile_id_for_paths(
        "maya",
        [str(tmp_path / "Documents" / "maya")],
        path=config_path
    ) == "default"


def test_custom_profile_root_removal_is_blocked_until_uninstalled(tmp_path):
    import pytest

    default_root = tmp_path / "maya"
    custom_root = tmp_path / "studio" / "maya"
    default_root.mkdir(parents=True)
    (custom_root / "2025").mkdir(parents=True)
    config_path = str(tmp_path / "dcc_integrations.json")

    record = add_profile_root(
        "maya",
        str(custom_root),
        label="Studio",
        path=config_path
    )
    adapter = MayaAdapter(
        distribution_path=str(tmp_path / "ScriptToolbox"),
        user_root=str(default_root),
        registry_reader=lambda: [
            ("2025", str(tmp_path / "Autodesk" / "Maya2025"))
        ],
        config_path=config_path
    )

    studio = _profile_installation(adapter, "2025", "Studio")
    adapter.install(studio)

    with pytest.raises(MayaIntegrationError):
        adapter.remove_profile_root(record["id"])

    adapter.uninstall(studio)
    assert adapter.remove_profile_root(record["id"]) is True
    assert get_profile_roots("maya", path=config_path) == []


def test_profile_root_config_add_is_idempotent_and_remove_is_scoped(tmp_path):
    config_path = str(tmp_path / "dcc_integrations.json")
    first_path = tmp_path / "profiles" / "one"
    second_path = tmp_path / "profiles" / "two"

    first = add_profile_root(
        "maya",
        str(first_path),
        label="First",
        path=config_path
    )
    duplicate = add_profile_root(
        "maya",
        str(first_path),
        label="Renamed",
        path=config_path
    )
    second = add_profile_root(
        "maya",
        str(second_path),
        label="Second",
        path=config_path
    )

    roots = get_profile_roots("maya", path=config_path)
    assert len(roots) == 2
    assert first["id"] == duplicate["id"]
    assert roots[0]["label"] == "Renamed"
    assert second["id"] != first["id"]

    assert remove_profile_root(
        "maya",
        first["id"],
        path=config_path
    ) is True
    remaining = get_profile_roots("maya", path=config_path)
    assert [item["id"] for item in remaining] == [second["id"]]
