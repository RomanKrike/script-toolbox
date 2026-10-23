# -*- coding: utf-8 -*-

import pytest
from pathlib import Path

from script_toolbox.integrations.base import STATUS_INSTALLED
from script_toolbox.integrations.base import STATUS_UPDATE_REQUIRED
from script_toolbox.integrations.icons import maya_shelf_icon_path
from script_toolbox.integrations.maya import MayaAdapter
from script_toolbox.integrations.maya import MayaIntegrationError
from script_toolbox.integrations.maya import _shelf_content
from script_toolbox.integrations.maya_shelf import resaved_shelf_button
from script_toolbox.integrations.maya_shelf import resaved_shelf_buttons


def _adapter(tmp_path):
    root = tmp_path / "maya"
    (root / "2025").mkdir(parents=True)
    adapter = MayaAdapter(
        distribution_path=str(tmp_path / "Toolbox Studio"),
        user_root=str(root),
        registry_reader=lambda: [("2025", str(tmp_path / "Maya2025"))],
        config_path=str(tmp_path / "dcc.json")
    )
    target = next(item for item in adapter.get_installations()
                  if item.version == "2025")
    adapter.install(target)
    return adapter, target


def _saved_shelf(adapter, legacy=False):
    content = _shelf_content(adapter.distribution_path)
    content = content.replace("// ScriptToolbox managed shelf\n", "")
    content = content.replace("global proc shelf_ScriptToolbox ()",
                              "global proc shelf_ScriptToolbox()")
    if legacy:
        content = content.replace('        -docTag "ScriptToolbox/launcher"\n', "")
        content = content.replace("import script_toolbox; script_toolbox.show()",
                                  "<function _open_toolbox at 0xABC123>")
        content = content.replace(maya_shelf_icon_path(adapter.distribution_path),
                                  "pythonFamily.png")
    return content


def test_maya_resave_without_comments_remains_installed(tmp_path):
    adapter, target = _adapter(tmp_path)
    path = tmp_path / "maya/2025/prefs/shelves/shelf_ScriptToolbox.mel"
    saved = _saved_shelf(adapter)
    path.write_text(saved, encoding="utf-8")
    assert adapter.status(target).state == STATUS_INSTALLED
    assert resaved_shelf_button(saved) is not None


def test_repair_recovers_old_callable_and_backs_up_the_resaved_file(tmp_path):
    adapter, target = _adapter(tmp_path)
    path = tmp_path / "maya/2025/prefs/shelves/shelf_ScriptToolbox.mel"
    saved = _saved_shelf(adapter, legacy=True)
    path.write_text(saved, encoding="utf-8")
    # A previous generic backup must not prevent saving this specific resave.
    path.with_name(path.name + ".script_toolbox.bak").write_text("earlier", encoding="utf-8")
    assert adapter.status(target).state == STATUS_UPDATE_REQUIRED
    assert adapter.repair(target).state == STATUS_INSTALLED
    backup = path.with_name(path.name + ".script_toolbox.resaved.bak")
    assert backup.read_text(encoding="utf-8") == saved
    repaired = path.read_text(encoding="utf-8")
    assert '-docTag "ScriptToolbox/launcher"' in repaired
    assert '<function ' not in repaired
    assert repaired.count("ScriptToolboxOpenButton") == 1
    assert adapter.repair(target).state == STATUS_INSTALLED


@pytest.mark.parametrize("extra", [
    'shelfButton -label "My Tool" -command "print(1)";',
    'print "keep custom startup";',
    '$custom = clearCache();',
])
def test_unmarked_shelf_with_other_controls_or_code_is_not_overwritten(tmp_path, extra):
    adapter, target = _adapter(tmp_path)
    path = tmp_path / "maya/2025/prefs/shelves/shelf_ScriptToolbox.mel"
    saved = _saved_shelf(adapter, legacy=True).replace("\n}", "\n" + extra + "\n}")
    path.write_text(saved, encoding="utf-8")
    assert resaved_shelf_button(saved) is None
    with pytest.raises(MayaIntegrationError, match="not managed"):
        adapter.repair(target)
    assert path.read_text(encoding="utf-8") == saved


def test_markerless_launcher_with_custom_double_click_stays_user_owned(tmp_path):
    adapter, unused = _adapter(tmp_path)
    saved = _saved_shelf(adapter).replace(
        '-sourceType "python"', '-doubleClickCommand "print(123)" -sourceType "python"'
    )
    assert resaved_shelf_button(saved) is None


def test_quoted_and_commented_shelf_button_words_are_not_extra_controls(tmp_path):
    adapter, unused = _adapter(tmp_path)
    saved = _saved_shelf(adapter).replace(
        '-style "iconOnly"', '-imageOverlayLabel "shelfButton; text" -style "iconOnly"'
    )
    saved += "\n// shelfButton; ignored comment\n"
    assert resaved_shelf_button(saved) is not None


def test_old_mel_wrapper_and_maya_buffer_declarations_are_recognized(tmp_path):
    adapter, unused = _adapter(tmp_path)
    saved = _saved_shelf(adapter).replace(
        "import script_toolbox; script_toolbox.show()",
        'python(\\"import script_toolbox; script_toolbox.show()\\")'
    )
    saved = saved.replace("\n{", '\n{\n global string $gBuffStr; $gBuffStr = "";')
    saved = saved.replace('-sourceType "python"', '-sourceType "mel"')
    assert resaved_shelf_button(saved) is not None


def test_uninstall_recognizes_and_backs_up_a_resaved_single_launcher(tmp_path):
    adapter, target = _adapter(tmp_path)
    path = tmp_path / "maya/2025/prefs/shelves/shelf_ScriptToolbox.mel"
    saved = _saved_shelf(adapter)
    path.write_text(saved, encoding="utf-8")
    adapter.uninstall(target)
    assert not path.exists()
    assert path.with_name(path.name + ".script_toolbox.resaved.bak").read_text(encoding="utf-8") == saved


@pytest.mark.parametrize("old_size", ["1024", "", "32"])
def test_repair_updates_resaved_oversized_or_unspecified_button(tmp_path, old_size):
    adapter, target = _adapter(tmp_path)
    path = tmp_path / "maya/2025/prefs/shelves/shelf_ScriptToolbox.mel"
    saved = _saved_shelf(adapter)
    for flag in ("width", "height"):
        saved = saved.replace("        -%s 34\n" % flag,
                              "        -%s %s\n" % (flag, old_size) if old_size else "")
    path.write_text(saved, encoding="utf-8")
    assert adapter.status(target).state == STATUS_UPDATE_REQUIRED
    assert adapter.repair(target).state == STATUS_INSTALLED
    repaired = path.read_text(encoding="utf-8")
    assert "-width 34" in repaired and "-height 34" in repaired
    assert path.with_name(path.name + ".script_toolbox.resaved.bak").read_text(encoding="utf-8") == saved


def _duplicate_saved_buttons(content):
    begin = content.index("    shelfButton")
    end = content.index('"ScriptToolboxOpenButton";', begin) + len('"ScriptToolboxOpenButton";')
    button = content[begin:end]
    copies = [button.replace('"ScriptToolboxOpenButton";', '"shelfButton%d";' % index)
              for index in range(3)]
    return content[:begin] + "\n".join(copies) + content[end:]


def test_repair_collapses_resaved_duplicates_and_repairs_command_and_icon(tmp_path):
    adapter, target = _adapter(tmp_path)
    path = tmp_path / "maya/2025/prefs/shelves/shelf_ScriptToolbox.mel"
    saved = _duplicate_saved_buttons(_saved_shelf(adapter, legacy=True))
    path.write_text(saved, encoding="utf-8")
    assert adapter.status(target).state == STATUS_UPDATE_REQUIRED
    assert adapter.repair(target).state == STATUS_INSTALLED
    repaired = path.read_text(encoding="utf-8")
    assert repaired == _shelf_content(adapter.distribution_path)
    assert path.with_name(path.name + ".script_toolbox.resaved.bak").read_text(encoding="utf-8") == saved
    assert adapter.repair(target).state == STATUS_INSTALLED


def test_current_but_duplicated_saved_buttons_still_require_repair(tmp_path):
    adapter, target = _adapter(tmp_path)
    path = tmp_path / "maya/2025/prefs/shelves/shelf_ScriptToolbox.mel"
    path.write_text(_duplicate_saved_buttons(_saved_shelf(adapter)), encoding="utf-8")
    assert adapter.status(target).state == STATUS_UPDATE_REQUIRED
    assert adapter.repair(target).state == STATUS_INSTALLED


def test_repair_recognizes_maya_escaped_newlines_around_broken_callable(tmp_path):
    adapter, target = _adapter(tmp_path)
    path = tmp_path / "maya/2025/prefs/shelves/shelf_ScriptToolbox.mel"
    saved = _saved_shelf(adapter, legacy=True).replace(
        '<function _open_toolbox at 0xABC123>',
        r'\n<function _open_toolbox at 0xABC123>\n'
    )
    path.write_text(saved, encoding="utf-8")
    assert adapter.repair(target).state == STATUS_INSTALLED
    assert '<function ' not in path.read_text(encoding="utf-8")


@pytest.mark.parametrize("extra", [
    'shelfButton -label "ScriptToolbox" -annotation "Open Script Toolbox" -command "print(1)";',
    'shelfButton -docTag "ScriptToolbox/launcher" -command "print(1)";',
    'print "keep custom startup";',
])
def test_duplicate_launchers_do_not_allow_overwriting_custom_shelf_code(tmp_path, extra):
    adapter, target = _adapter(tmp_path)
    path = tmp_path / "maya/2025/prefs/shelves/shelf_ScriptToolbox.mel"
    saved = _duplicate_saved_buttons(_saved_shelf(adapter, legacy=True))
    saved = saved.replace("\n}", "\n" + extra + "\n}")
    path.write_text(saved, encoding="utf-8")
    with pytest.raises(MayaIntegrationError, match="not managed"):
        adapter.repair(target)
    assert path.read_text(encoding="utf-8") == saved


def test_repair_actual_maya_2025_saved_callback_paths(tmp_path):
    adapter, target = _adapter(tmp_path)
    path = tmp_path / "maya/2025/prefs/shelves/shelf_ScriptToolbox.mel"
    saved = (Path(__file__).parent / "fixtures" / "maya_2025_legacy_shelf.mel").read_text(encoding="utf-8")
    path.write_text(saved, encoding="utf-8")
    assert len(resaved_shelf_buttons(saved)) == 3
    assert adapter.status(target).state == STATUS_UPDATE_REQUIRED
    assert adapter.repair(target).state == STATUS_INSTALLED
    assert path.read_text(encoding="utf-8") == _shelf_content(adapter.distribution_path)
    backup = path.with_name(path.name + ".script_toolbox.resaved.bak")
    assert backup.read_text(encoding="utf-8") == saved


@pytest.mark.parametrize("command", [
    "other_module._open_toolbox",
    "script_toolbox.integrations.maya_runtime._open_toolbox_custom",
    "script_toolbox.integrations.maya_runtime._open_toolbox; print(1)",
])
def test_saved_callback_path_does_not_accept_unrelated_or_extra_commands(tmp_path, command):
    adapter, unused = _adapter(tmp_path)
    saved = _saved_shelf(adapter).replace("import script_toolbox; script_toolbox.show()", command)
    assert resaved_shelf_button(saved) is None
