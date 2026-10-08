"""Real Qt integration: reference creation, staged editing and persistence."""
import pytest
from test_qt_lifecycle import run_qt as _run_qt, QT_AVAILABLE

pytestmark = pytest.mark.skipif(not QT_AVAILABLE, reason="Requires real Qt")


WAIT = """
def wait_job(owner, attribute):
    until = time.monotonic() + 10
    while getattr(owner, attribute) is not None and time.monotonic() < until:
        pump(0.03)
    assert getattr(owner, attribute) is None

def wait_snapshot(owner):
    until = time.monotonic() + 5
    while owner.preset_snapshot_loader.busy and time.monotonic() < until:
        pump(0.03)
    assert not owner.preset_snapshot_loader.busy

def apply_and_wait(editor):
    result = editor.apply_changes()
    if result is None:
        wait_snapshot(editor)
        result = editor.last_apply_result
    return result
"""


def run_qt(body, tmp_path):
    body = body.replace('w.open_interface_editor()', 'w.open_interface_editor(); wait_snapshot(w.editor_window)')
    body = body.replace('assert editor.apply_changes()', 'assert apply_and_wait(editor)')
    body = body.replace('w.reload_config()', 'w.reload_config(); wait_snapshot(w)')
    _run_qt(WAIT + body, tmp_path)


def test_reference_ui_create_apply_undo_reload_and_convert(tmp_path):
    run_qt('''
import json
from script_toolbox.core.preset_sources import SourceRegistry
from script_toolbox.core.preset_sync import SyncService, MANIFEST
from script_toolbox.core.config import config_path
from script_toolbox.model import create_item
from script_toolbox.ui.managed_presets import target_address
from script_toolbox.ui.preset_hooks import _convert_reference
remote = os.path.join(os.path.dirname(config_path()), "fixture_remote")
os.makedirs(remote)
target = create_item("menu", {"id": "shots", "name": "shots", "ui": {"label": "Shots"},
                              "props": {"items": ["sh001", "sh002"]}})
preset = {"id": "pipeline", "dcc": "all", "root": target}
payload = json.dumps(preset).encode("utf-8")
os.makedirs(os.path.join(remote, "All", "General"))
with open(os.path.join(remote, "All", "General", "pipeline.json"), "wb") as handle:
    handle.write(payload)
manifest = {"schema": 1, "id": "studio", "name": "Studio"}
with open(os.path.join(remote, MANIFEST), "w") as handle:
    json.dump(manifest, handle)
registry = SourceRegistry()
registry.put({"id": "studio", "name": "Studio", "remote_path": remote})
assert SyncService(registry).check("studio", True)["state"] == "up_to_date"
assert "studio" not in w.preset_resolver.sources  # active runtime stays pinned
w.open_interface_editor()
editor = w.editor_window
palette_item = None
for i in range(editor.preset_palette.topLevelItemCount()):
    group = editor.preset_palette.topLevelItem(i)
    for j in range(group.childCount()):
        category = group.child(j)
        for k in range(category.childCount()):
            candidate = category.child(k)
            if target_address(candidate):
                palette_item = candidate
assert palette_item is not None
editor.create_from_preset(palette_item)
ref_id = editor.current_item_id
assert editor.item_cache[ref_id]["kind"] == "reference"
assert type(editor.current_property_editor).__name__ == "ReferenceInfoLabel"
assert editor.apply_changes()
assert w.find_item(ref_id)["kind"] == "menu"
assert editor.item_cache[ref_id]["kind"] == "reference"
w.store_value(ref_id, "sh002")
w.flush_pending_save()
with open(config_path()) as handle:
    saved = json.load(handle)
assert saved["sections"][0]["items"][0]["kind"] == "reference"
assert saved["sections"][0]["items"][0]["props"]["state"]["value"] == "sh002"
editor._call_tree_action("Convert Reference", _convert_reference, ref_id)
assert editor.item_cache[ref_id]["kind"] == "menu"
editor.undo()
assert editor.item_cache[ref_id]["kind"] == "reference"
editor.redo()
assert editor.item_cache[ref_id]["kind"] == "menu"
editor.close()
w.reload_config()
assert w.find_item(ref_id)["props"]["value"] == "sh002"
assert w.close()
w.deleteLater()
pump()
''', tmp_path)


def test_settings_page_and_worker_can_close_during_sync(tmp_path):
    run_qt('''
from script_toolbox.ui.settings_dialog import SettingsDialog
dialog = SettingsDialog(w)
labels = [dialog.category_list.item(i).text() for i in range(dialog.category_list.count())]
assert "Preset Library" in labels
page = dialog.pages.widget(labels.index("Preset Library"))
page.start(lambda: time.sleep(0.2))
dialog.close()
dialog.deleteLater()
pump(0.4)
assert w.close()
w.deleteLater()
pump()
''', tmp_path)


def test_library_create_save_and_nested_catalog(tmp_path):
    run_qt('''
update_ui.check_for_update = lambda **kw: {"available": False}
from script_toolbox.ui.settings_dialog import SettingsDialog
from script_toolbox.core.preset_sources import SourceRegistry
from script_toolbox.core.preset_references import PresetResolver
from script_toolbox.ui.managed_presets import library_address
from script_toolbox.ui.preset_hooks import _filter_preset_tree
from script_toolbox.model import create_item
remote = os.path.join(os.path.dirname(SourceRegistry().cache_root), "new_library")
os.makedirs(remote)
dialog = SettingsDialog(w)
labels = [dialog.category_list.item(i).text() for i in range(dialog.category_list.count())]
page = dialog.pages.widget(labels.index("Preset Library"))
assert page.list.item(0).text().startswith("Default")
assert not page.buttons[2].isEnabled()
QtGui.QFileDialog.getExistingDirectory = lambda *a, **k: remote
QtGui.QInputDialog.getText = lambda *a, **k: ("0+Media", True)
page.create_library()
wait_job(page, 'job')
assert page.job is None
registry = SourceRegistry()
assert len(registry.sources()) == 1
dialog.close()
w.open_interface_editor()
editor = w.editor_window
root = create_item("folder", {"id":"fixture-leo", "name":"leo", "ui":{"label":"Leo"}, "items":[
    create_item("menu", {"id":"fixture-shots","name":"shots","props":{"items":["sh001","sh002"]}}),
    create_item("button", {"id":"fixture-open","name":"open_shot","bindings":[
        {"event":"click","handler":"script","script":'value = toolbox.get_value("shots")'}]})]})
editor.sync_working_from_tree()
selected = editor._insert_cloned_tree_item(root, sibling=False)
editor.tree.setCurrentItem(selected)
editor.tree_changed()
assert editor.current_item_id == "fixture-leo"
from script_toolbox.ui.managed_presets import SavePresetDialog
from script_toolbox.compat import QtCore
def cancel_save():
    form = app.activeModalWidget()
    assert isinstance(form, SavePresetDialog)
    form.reject()
QtCore.QTimer.singleShot(0, cancel_save)
editor.save_selected_preset()
assert editor._preset_save_job is None
assert PresetResolver(registry).packages[registry.sources()[0]["id"]]["presets"] == []
def fill_save():
    form = app.activeModalWidget()
    assert isinstance(form, SavePresetDialog)
    assert form.name_edit.text() == "Leo"
    form.name_edit.setText(" ")
    assert not form.buttons.button(QtGui.QDialogButtonBox.Save).isEnabled()
    form.name_edit.setText("Leo")
    form.category_edit.setText("Project Pipeline/Animation")
    assert form.buttons.button(QtGui.QDialogButtonBox.Save).isEnabled()
    form.accept()
original_resolver = editor.preset_resolver
assert editor.apply_changes()
applied_resolver = w.preset_resolver
assert applied_resolver is editor.preset_resolver
assert applied_resolver is not original_resolver
editor.palette_filter.setText("unrelated")
QtCore.QTimer.singleShot(0, fill_save)
editor.save_selected_preset()
wait_job(editor, '_preset_save_job')
assert editor._preset_save_job is None
assert w.preset_resolver is applied_resolver
assert editor.preset_resolver is not original_resolver
assert editor.palette_filter.text() == ""
assert editor.palette_tabs.currentIndex() == 1
resolver = PresetResolver(registry)
source_id = registry.sources()[0]["id"]
assert resolver.packages[source_id]["presets"][0]["category"] == "Project Pipeline/Animation"
assert original_resolver.packages[source_id]["presets"] == []
default = editor.preset_palette.topLevelItem(0)
assert default.text(0) == "Default"
assert default.child(0).text(0) == "Selection"
assert default.child(0).child(0).text(0) == "Selection Set"
studio = editor.preset_palette.topLevelItem(1)
assert studio.child(0).child(0).text(0) == "Animation"
preset_item = studio.child(0).child(0).child(0)
assert studio.text(0) == "0+Media"
assert studio.child(0).text(0) == "Project Pipeline"
assert preset_item.text(0) == "Leo"
assert library_address(preset_item)[0] == source_id
assert editor.preset_palette.currentItem() is preset_item
_filter_preset_tree(editor.preset_palette, "Leo")
assert default.isHidden() and not studio.isHidden()
_filter_preset_tree(editor.preset_palette, "")
import script_toolbox.core.preset_library as publisher
publish = publisher.publish_presets
warnings = []
def fail_publish(*args, **kwargs):
    raise IOError("fixture: library is read-only")
publisher.publish_presets = fail_publish
QtGui.QMessageBox.warning = lambda *args: warnings.append(args[2])
QtCore.QTimer.singleShot(0, fill_save)
editor.save_selected_preset()
wait_job(editor, '_preset_save_job')
assert editor._preset_save_job is None
assert warnings == ["fixture: library is read-only"]
assert editor.preset_palette.currentItem() is preset_item
assert len(PresetResolver(registry).packages[source_id]["presets"]) == 1
publisher.publish_presets = publish
editor.create_from_preset(preset_item)
linked_id = editor.current_item_id
assert editor.item_cache[linked_id]["items"][0]["kind"] == "reference"
assert editor.apply_changes()
from script_toolbox.model import walk_items
linked = next(i for i in walk_items(w.config, include_sections=True) if i["id"] == linked_id)
assert linked["items"][0]["kind"] == "menu"
assert 'get_value("{0}")'.format(linked["items"][0]["name"]) in linked["items"][1]["bindings"][0]["script"]
editor.close()
assert w.close()
w.deleteLater()
pump()
''', tmp_path)


def test_apply_activates_latest_library_without_losing_staged_values(tmp_path):
    run_qt('''
import copy
from script_toolbox.core.preset_sources import SourceRegistry
from script_toolbox.core.preset_library import publish_presets
from script_toolbox.core.preset_sync import SyncService
from script_toolbox.model import create_item
registry = SourceRegistry()
remote = os.path.join(os.path.dirname(registry.cache_root), "apply-library")
target = create_item("menu", {"id":"shots", "name":"shots", "ui":{"label":"Before sync"},
                              "props":{"items":["sh001","sh002"]}})
preset = {"id":"shots-preset", "label":"Shots", "root":target}
publish_presets([preset], remote, "studio", "Studio")
registry.put({"id":"studio", "name":"Studio", "remote_path":remote})
assert SyncService(registry).check("studio", True)["state"] == "up_to_date"
w.reload_config()
reference = w.preset_resolver.create_reference("studio", "shots-preset", "shots")
reference["props"]["state"]["value"] = "sh002"
w.config = {"version":21, "sections":[create_item("folder", {
    "id":"root", "name":"root", "items":[reference]})]}
w.save()
w.rebuild()
w.open_interface_editor()
editor = w.editor_window
old_snapshot = editor.preset_resolver
# A staged edit must survive activation of the latest library snapshot.
editor.item_cache["root"]["ui"]["label"] = "Local staged folder"
editor.populate_tree()
updated = copy.deepcopy(preset)
updated["root"]["ui"]["label"] = "After sync"
updated["root"]["props"]["items"].append("sh003")
publish_presets([updated], remote, "studio", "Studio")
assert SyncService(registry).check("studio", True)["state"] == "up_to_date"
# Applying must only read local snapshots, including when the share is offline.
import shutil
shutil.rmtree(remote)
assert editor.apply_changes()
assert w.preset_resolver is not old_snapshot
assert w.find_item(reference["id"])["ui"]["label"] == "After sync"
assert w.get_value(reference["id"]) == "sh002"
assert w.config["sections"][0]["ui"]["label"] == "Local staged folder"
assert "sh003" in w.find_item(reference["id"])["props"]["items"]
# Reload followed by Apply from the same editor cannot reactivate the old cache.
w.reload_config()
assert editor.apply_changes()
assert w.find_item(reference["id"])["ui"]["label"] == "After sync"
assert w.get_value(reference["id"]) == "sh002"
editor.close()
assert w.close()
w.deleteLater()
pump()
''', tmp_path)


def test_standalone_library_host_choice_and_catalog_filter(tmp_path):
    run_qt('''
from script_toolbox.core.preset_sources import SourceRegistry
from script_toolbox.core.preset_library import publish_presets
from script_toolbox.core.preset_sync import SyncService
from script_toolbox.core.preset_references import PresetResolver
from script_toolbox.model import create_item
from script_toolbox.ui import managed_presets as managed
registry = SourceRegistry()
remote = os.path.join(os.path.dirname(registry.cache_root), "host-library")
root = create_item("button", {"id": "button", "name": "button"})
definitions = [{"id": key, "label": key, "category": "Utilities", "dcc": key, "root": root}
               for key in ("all", "standalone", "maya")]
publish_presets(definitions, remote, "hosts", "Hosts")
registry.put({"id": "hosts", "name": "Hosts", "remote_path": remote})
assert os.path.isfile(os.path.join(remote, "Standalone", "Utilities", "standalone.json"))
assert SyncService(registry).check("hosts", True)["state"] == "up_to_date"
form = managed.SavePresetDialog(registry.sources(), "Watch", w)
index = form.host.findText("standalone")
assert index >= 0
form.host.setCurrentIndex(index)
assert form.values()["dcc"] == "standalone"
form.close()
form.deleteLater()
owner = type("Owner", (object,), {})()
owner.preset_resolver = PresetResolver(registry)
tree = QtGui.QTreeWidget()
managed.populate_managed_presets(owner, tree)
category = tree.topLevelItem(0).child(0)
assert [category.child(i).text(0) for i in range(category.childCount())] == ["all", "standalone"]
managed.HOST = type("MayaHost", (object,), {"key": "maya"})()
tree.clear()
managed.populate_managed_presets(owner, tree)
category = tree.topLevelItem(0).child(0)
assert [category.child(i).text(0) for i in range(category.childCount())] == ["all", "maya"]
tree.deleteLater()
assert w.close()
w.deleteLater()
pump()
''', tmp_path)
