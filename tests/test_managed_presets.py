import copy
import json
import shutil

import pytest

from script_toolbox.constants import CONFIG_VERSION
from script_toolbox.core.config import serialize_config, deserialize_config
from script_toolbox.core.preferences import save_preferences, load_preferences
from script_toolbox.core.preset_sources import SourceRegistry
from script_toolbox.core.preset_sync import SyncService, MANIFEST, source_file, InvalidSource
from script_toolbox.core.preset_references import PresetResolver, authored_document, local_copy
from script_toolbox.model import create_item, normalize_document


def publish(folder, source_id="studio", revision=1, label="Shots", kind="menu", missing=False):
    folder.mkdir(parents=True, exist_ok=True)
    target = create_item(kind, {"id": "shots", "name": "shots",
                               "ui": {"label": label},
                               "props": {"items": ["sh001", "sh002"]} if kind == "menu" else {}})
    preset = {"id": "pipeline", "dcc": "all", "label": "Pipeline",
              "description": "fixture generation {0}".format(revision),
              "root": create_item("folder", {"id": "root", "items": [] if missing else [target]})}
    payload = json.dumps(preset).encode("utf-8")
    (folder / "All" / "General").mkdir(parents=True, exist_ok=True)
    (folder / "All" / "General" / "pipeline.json").write_bytes(payload)
    manifest = {"schema": 1, "id": source_id, "name": "Studio"}
    (folder / MANIFEST).write_text(json.dumps(manifest), encoding="utf-8")
    return manifest


@pytest.fixture
def setup(tmp_path):
    remote = tmp_path / "remote"
    publish(remote)
    registry = SourceRegistry(str(tmp_path / "settings.json"), str(tmp_path / "cache"))
    registry.put({"id": "studio", "name": "Studio", "remote_path": str(remote)})
    return remote, registry, SyncService(registry)


def document(reference):
    return {"version": CONFIG_VERSION,
            "sections": [create_item("folder", {"id": "local", "items": [reference]})]}


def first(doc):
    return doc["sections"][0]["items"][0]


def test_registry_edits_preserve_identity_and_unrelated_preferences(setup):
    remote, registry, service = setup
    save_preferences({"custom": {"untouched": True}}, registry.preferences_path)
    source = registry.get("studio")
    source.update(name="Renamed", enabled=False, remote_path=str(remote / "other"))
    registry.put(source)
    assert registry.get("studio")["name"] == "Renamed"
    assert load_preferences(registry.preferences_path)["custom"] == {"untouched": True}
    assert len(registry.sources()) == 1
    registry.remove("studio")
    assert registry.sources() == []
    assert remote.exists()


def test_registry_pins_host_paths_before_background_connection(tmp_path, monkeypatch):
    import threading
    import script_toolbox.core.preset_sources as sources
    import script_toolbox.core.preferences as preferences
    main_thread = threading.current_thread()
    maya_preferences = str(tmp_path / "maya-settings.json")
    standalone_preferences = str(tmp_path / "standalone-settings.json")
    calls = []
    def host_path():
        calls.append(threading.current_thread())
        return maya_preferences if threading.current_thread() is main_thread else standalone_preferences
    monkeypatch.setattr(sources, "settings_path", host_path)
    monkeypatch.setattr(preferences, "settings_path", host_path)
    monkeypatch.setattr(sources, "user_config_dir", lambda: str(tmp_path / "maya"))
    source = {"id": "studio", "name": "Studio", "remote_path": str(tmp_path / "remote")}
    standalone = SourceRegistry(standalone_preferences, str(tmp_path / "standalone-cache"))
    standalone.put(source)
    original = (tmp_path / "standalone-settings.json").read_bytes()
    registry = SourceRegistry()
    assert registry.preferences_path == maya_preferences
    assert registry.sources() == []
    results = []
    def connect():
        try:
            results.append(registry.get("studio"))
            registry.put(source)
            results.append(registry.get("studio"))
            results.append(registry.cache_path("studio"))
        except Exception as error:
            results.append(error)
    worker = threading.Thread(target=connect)
    worker.start()
    worker.join(timeout=5)
    assert not worker.is_alive()
    assert results[0] is None
    assert results[1]["id"] == "studio"
    assert results[2] == str(tmp_path / "maya" / "presets" / "managed" / "studio")
    assert len(registry.sources()) == 1
    assert (tmp_path / "standalone-settings.json").read_bytes() == original
    assert calls and all(thread is main_thread for thread in calls)


def test_first_sync_offline_and_update(setup):
    remote, registry, service = setup
    assert service.status("studio")["state"] == "not_installed"
    assert service.check("studio")["state"] == "update_available"
    one = service.check("studio", True)["local_revision"]
    assert one
    assert service.check("studio")["state"] == "up_to_date"
    publish(remote, revision=2)
    assert service.check("studio")["state"] == "update_available"
    two = service.check("studio", True)["local_revision"]
    assert two != one
    shutil.rmtree(str(remote))
    status = service.check("studio", True)
    assert status["state"] == "offline"
    assert status["using_cache"] and status["local_revision"] == two


def test_offline_first_connection_and_disabled_do_not_fetch(setup, monkeypatch):
    remote, registry, service = setup
    shutil.rmtree(str(remote))
    status = service.check("studio", True)
    assert status["state"] == "offline" and not status["using_cache"]
    source = registry.get("studio")
    source["enabled"] = False
    registry.put(source)
    import script_toolbox.core.preset_sync as sync
    monkeypatch.setattr(sync, "read_json", lambda *args: (_ for _ in ()).throw(AssertionError("network read")))
    monkeypatch.setattr(service, "status", lambda *args: {"state": "offline"})
    assert service.check("studio", True)["state"] == "offline"
    assert not service.due(source, startup=True)


@pytest.mark.parametrize("failure", ["checksum", "json", "source_id", "schema", "target_ids", "copy"])
def test_failed_sync_keeps_current_and_user_files(setup, tmp_path, monkeypatch, failure):
    remote, registry, service = setup
    service.check("studio", True)
    pointer = (tmp_path / "cache" / "studio" / "active.json").read_bytes()
    user = tmp_path / "user.json"
    user.write_bytes(b"user content")
    manifest = publish(remote, revision=2)
    if failure == "checksum":
        (remote / "All" / "General" / "pipeline.json").write_text("{}")
    elif failure == "json":
        payload = b"broken json"
        (remote / "All" / "General" / "pipeline.json").write_bytes(payload)
    elif failure == "target_ids":
        data = json.loads((remote / "All" / "General" / "pipeline.json").read_text())
        data["root"]["items"].append(copy.deepcopy(data["root"]["items"][0]))
        payload = json.dumps(data).encode("utf-8")
        (remote / "All" / "General" / "pipeline.json").write_bytes(payload)
    elif failure == "source_id":
        manifest["id"] = "other"
    elif failure == "schema":
        manifest["schema"] = 99
    elif failure == "copy":
        def fail(*args):
            raise IOError("disk full")
        monkeypatch.setattr("script_toolbox.core.preset_sync.shutil.copyfile", fail)
    (remote / MANIFEST).write_text(json.dumps(manifest))
    assert service.check("studio", True)["state"] in ("invalid_source", "sync_failed")
    assert (tmp_path / "cache" / "studio" / "active.json").read_bytes() == pointer
    assert service.installed("studio")["presets"][0]["description"] == "fixture generation 1"
    assert user.read_bytes() == b"user content"
    assert not list((tmp_path / "cache" / "studio").glob(".staging-*"))


def test_manifest_changes_during_copy_rejects_activation(setup, monkeypatch):
    remote, registry, service = setup
    service.check("studio", True)
    publish(remote, revision=2)
    original = shutil.copyfile
    def changing_copy(*args):
        result = original(*args)
        publish(remote, revision=3)
        return result
    monkeypatch.setattr("script_toolbox.core.preset_sync.shutil.copyfile", changing_copy)
    assert service.check("studio", True)["state"] == "invalid_source"
    assert service.installed("studio")["presets"][0]["description"] == "fixture generation 1"


@pytest.mark.parametrize("path", ["../escape.json", "/absolute.json", "C:\\outside.json",
                                  "\\\\server\\file.json", "folder/../../file", "folder\\..\\file",
                                  "a:stream", "./file", ""])
def test_paths_cannot_escape_source(tmp_path, path):
    with pytest.raises(InvalidSource):
        source_file(str(tmp_path), path)


def test_symlink_escape_rejected(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text("{}")
    (root / "link.json").symlink_to(outside)
    with pytest.raises(InvalidSource):
        source_file(str(root), "link.json")


def test_resolve_save_reload_preserves_link_and_local_value(setup):
    remote, registry, service = setup
    service.check("studio", True)
    resolver = PresetResolver(registry)
    reference = resolver.create_reference("studio", "pipeline", "shots", name="my_shots")
    assert reference["kind"] == "reference" and reference["id"] != "shots"
    runtime = resolver.resolve_document(document(reference))
    item = first(runtime)
    assert item["kind"] == "menu" and item["name"] == "my_shots"
    assert item["id"] == reference["id"]
    item["props"]["value"] = "sh002"
    text = serialize_config(runtime)
    assert "_preset_reference" not in text
    persisted = deserialize_config(text)
    link = first(persisted)
    assert link["kind"] == "reference"
    assert link["props"]["state"] == {"value": "sh002"}
    assert "items" not in link["props"]
    assert first(resolver.resolve_document(persisted))["props"]["value"] == "sh002"
    assert first(runtime)["kind"] == "menu"  # serialization doesn't mutate runtime
    assert first(authored_document(normalize_document(runtime)))["kind"] == "reference"


def test_revision_is_pinned_and_missing_target_stays_visible(setup):
    remote, registry, service = setup
    service.check("studio", True)
    old = PresetResolver(registry)
    reference = old.create_reference("studio", "pipeline", "shots")
    publish(remote, revision=2, label="New shots")
    service.check("studio", True)
    new = PresetResolver(registry)
    assert old.resolve(reference)["ui"]["label"] == "Shots"
    assert new.resolve(reference)["ui"]["label"] == "New shots"
    publish(remote, revision=3, missing=True)
    service.check("studio", True)
    broken = PresetResolver(registry).resolve_document(document(reference))
    assert first(broken)["kind"] == "reference"
    assert "not found" in first(broken)["ui"]["tooltip"]
    assert first(deserialize_config(serialize_config(broken)))["props"]["parameter"] == "shots"


def test_offline_resolve_convert_remove_and_source_namespaces(setup, tmp_path):
    remote, registry, service = setup
    service.check("studio", True)
    second = tmp_path / "second"
    publish(second, source_id="project", label="Project shots")
    registry.put({"id": "project", "remote_path": str(second)})
    service.check("project", True)
    shutil.rmtree(str(remote))
    resolver = PresetResolver(registry)
    ref = resolver.create_reference("studio", "pipeline", "shots")
    other = resolver.create_reference("project", "pipeline", "shots")
    assert resolver.resolve(ref)["ui"]["label"] == "Shots"
    assert resolver.resolve(other)["ui"]["label"] == "Project shots"
    assert local_copy(ref, resolver)["kind"] == "menu"
    assert "_preset_reference" not in local_copy(ref, resolver)
    doc = document(ref)
    doc["sections"][0]["items"] = []
    assert service.installed("studio") is not None
    registry.remove("studio")
    assert first(PresetResolver(registry).resolve_document(document(ref)))["kind"] == "reference"


def test_type_change_breaks_reference_without_resetting_saved_value(setup):
    remote, registry, service = setup
    service.check("studio", True)
    ref = PresetResolver(registry).create_reference("studio", "pipeline", "shots")
    ref["props"]["state"] = {"value": "sh002"}
    publish(remote, revision=2, kind="string")
    service.check("studio", True)
    broken = first(PresetResolver(registry).resolve_document(document(ref)))
    assert broken["kind"] == "reference"
    assert broken["props"]["state"] == {"value": "sh002"}


def test_corrupt_current_uses_previous_generation(setup, tmp_path):
    remote, registry, service = setup
    service.check("studio", True)
    publish(remote, revision=2)
    service.check("studio", True)
    root = tmp_path / "cache" / "studio"
    pointer = json.loads((root / "active.json").read_text())
    (root / pointer["current"] / "All" / "General" / "pipeline.json").write_text("corrupt")
    assert service.installed("studio")["presets"][0]["description"] == "fixture generation 1"


def test_legacy_document_is_unchanged_by_resolver_and_serialization(setup):
    remote, registry, service = setup
    legacy = document(create_item("button", {"id": "local_button"}))
    before = copy.deepcopy(legacy)
    assert PresetResolver(registry).resolve_document(legacy) == before
    assert deserialize_config(serialize_config(legacy)) == before


def test_publication_is_complete_and_revision_is_automatic(tmp_path):
    from tools.publish_preset_source import publish as publish_source
    inputs, output = tmp_path / "inputs", tmp_path / "published"
    publish(inputs)
    (inputs / MANIFEST).unlink()
    one = publish_source(str(inputs), str(output), "studio", "Studio")
    assert one["revision"]
    two = publish_source(str(inputs), str(output), "studio", "Studio")
    assert one == two
    assert one["presets"][0]["file"] == "All/General/Pipeline.json"
    (inputs / "All" / "General" / "pipeline.json").write_text("broken")
    with pytest.raises(ValueError):
        publish_source(str(inputs), str(output), "studio", "Studio")
    assert json.loads((output / MANIFEST).read_text()) == {"schema": 1, "id": "studio", "name": "Studio"}


def test_manual_edits_are_detected_and_local_cache_is_bounded(setup, tmp_path):
    remote, registry, service = setup
    service.check("studio", True)
    publish(remote, revision=1, label="Changed without revision")
    assert service.check("studio", True)["state"] == "up_to_date"
    for revision in (2, 3, 4):
        publish(remote, revision=revision)
        assert service.check("studio", True)["state"] == "up_to_date"
    assert len(list((tmp_path / "cache" / "studio").glob("generation-*"))) == 2


def test_failed_atomic_activation_preserves_working_generation(setup, monkeypatch):
    remote, registry, service = setup
    service.check("studio", True)
    publish(remote, revision=2)
    import script_toolbox.core.preset_sync as sync
    original = sync.atomic_json
    def fail_activation(path, data):
        if path.endswith("active.json"):
            raise IOError("activation failed")
        return original(path, data)
    monkeypatch.setattr(sync, "atomic_json", fail_activation)
    assert service.check("studio", True)["state"] == "sync_failed"
    assert service.installed("studio")["presets"][0]["description"] == "fixture generation 1"


def test_reference_schema_protects_old_loader_and_only_changes_opt_in_documents(setup):
    from script_toolbox.core.config_schema import validate_document_schema, FutureConfigVersionError
    remote, registry, service = setup
    service.check("studio", True)
    resolver = PresetResolver(registry)
    reference = resolver.create_reference("studio", "pipeline", "shots")
    encoded = serialize_config(document(reference))
    assert json.loads(encoded)["version"] == 22
    with pytest.raises(FutureConfigVersionError):
        validate_document_schema(json.loads(encoded), expected_version=21)
    loaded = deserialize_config(encoded)
    assert first(loaded)["kind"] == "reference"
    first(loaded).clear()
    first(loaded).update(local_copy(reference, resolver))
    assert json.loads(serialize_config(loaded))["version"] == 21


def test_reference_rewrites_self_id_and_name_in_bindings(setup):
    remote, registry, service = setup
    data = json.loads((remote / "All" / "General" / "pipeline.json").read_text())
    target = data["root"]["items"][0]
    target["id"] = "source-shot-id"
    target["bindings"] = [{"event": "value_changed", "handler": "script", "language": "python",
                           "script": 'a = toolbox.get_value("source-shot-id")\nb = toolbox.get_value("shots")'}]
    payload = json.dumps(data).encode("utf-8")
    (remote / "All" / "General" / "pipeline.json").write_bytes(payload)
    manifest = json.loads((remote / MANIFEST).read_text())
    (remote / MANIFEST).write_text(json.dumps(manifest))
    service.check("studio", True)
    resolver = PresetResolver(registry)
    reference = resolver.create_reference("studio", "pipeline", "source-shot-id", name="local_shots")
    script = resolver.resolve(reference)["bindings"][0]["script"]
    assert 'get_value("{0}")'.format(reference["id"]) in script
    assert 'get_value("local_shots")' in script


def test_nonstring_published_ids_are_rejected(setup):
    remote, registry, service = setup
    data = json.loads((remote / "All" / "General" / "pipeline.json").read_text())
    data["root"]["items"][0]["id"] = 123
    payload = json.dumps(data).encode("utf-8")
    (remote / "All" / "General" / "pipeline.json").write_bytes(payload)
    manifest = json.loads((remote / MANIFEST).read_text())
    (remote / MANIFEST).write_text(json.dumps(manifest))
    assert service.check("studio", True)["state"] == "invalid_source"


def test_shipped_demo_source_is_valid():
    from pathlib import Path
    from script_toolbox.core.preset_sync import load_package
    root = Path(__file__).resolve().parents[1] / "examples" / "preset-source"
    package = load_package(str(root), "demo-studio")
    assert package["presets"][0]["root"]["name"] == "demo_shot"
