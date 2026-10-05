"""Real Qt integration: reference creation, staged editing and persistence."""
import pytest
from test_qt_lifecycle import run_qt, QT_AVAILABLE

pytestmark = pytest.mark.skipif(not QT_AVAILABLE, reason="Requires real Qt")


def test_reference_ui_create_apply_undo_reload_and_convert(tmp_path):
    run_qt('''
import json, hashlib
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
with open(os.path.join(remote, "pipeline.json"), "wb") as handle:
    handle.write(payload)
manifest = {"schema": 1, "id": "studio", "name": "Studio", "revision": 1,
            "presets": [{"id": "pipeline", "file": "pipeline.json",
                         "sha256": hashlib.sha256(payload).hexdigest()}]}
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
        candidate = group.child(j)
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
assert "Preset Sources" in labels
page = dialog.pages.widget(labels.index("Preset Sources"))
page.start(lambda: time.sleep(0.2))
dialog.close()
dialog.deleteLater()
pump(0.4)
assert w.close()
w.deleteLater()
pump()
''', tmp_path)
