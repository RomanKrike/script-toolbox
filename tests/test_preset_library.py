import copy
import pytest
from script_toolbox.core.preset_library import publish_presets
from script_toolbox.core.preset_sync import load_package, SyncService, MANIFEST
from script_toolbox.core.preset_sources import SourceRegistry
from script_toolbox.core.preset_references import PresetResolver, linked_preset, authored_document
from script_toolbox.core.editor_document import EditorDocumentController
from script_toolbox.core.config import serialize_config, deserialize_config
from script_toolbox.model import create_item


def fixture(tmp_path):
    root = create_item('folder', {'id': 'root', 'name': 'pipeline', 'items': [
        create_item('menu', {'id': 'shots', 'name': 'shots', 'props': {'items': ['sh001','sh002']}}),
        create_item('button', {'id': 'open', 'name': 'open', 'bindings': [
            {'event': 'click', 'handler': 'script', 'language': 'python',
             'script': 'shot = toolbox.get_value("shots")'}]})]})
    remote = str(tmp_path / 'remote')
    publish_presets([{'id': 'leo', 'label': 'Leo', 'category': 'Project Pipeline', 'dcc': 'all', 'root': root}], remote, 'studio', '0+Media')
    registry = SourceRegistry(str(tmp_path/'prefs.json'),str(tmp_path/'cache'))
    registry.put({'id':'studio','name':'0+Media','remote_path':remote})
    SyncService(registry).check('studio',True)
    return root, remote, PresetResolver(registry)


def test_publish_merge_and_invalid_revision_keeps_previous(tmp_path):
    root, remote, resolver = fixture(tmp_path)
    publish_presets([{'id':'extra','root':root}],remote,'studio','0+Media',merge=True)
    assert [p['id'] for p in load_package(remote)['presets']] == ['extra','leo']
    manifest = (tmp_path/'remote'/MANIFEST).read_bytes()
    with pytest.raises(ValueError):
        publish_presets([{'id':'broken','root':{'kind':'invalid','id':'x'}}],remote,'studio','0+Media',merge=True)
    assert (tmp_path/'remote'/MANIFEST).read_bytes() == manifest


def test_linked_bundle_roundtrip_duplicate_and_pinned_update(tmp_path):
    root, remote, resolver = fixture(tmp_path)
    controller = EditorDocumentController({'version':21,'sections':[root]})
    clone = controller.clone_subtree(root)
    linked = linked_preset(root,clone,'studio','leo',resolver)
    document = {'version':22,'sections':[linked]}
    reloaded = deserialize_config(serialize_config(document))
    runtime = resolver.resolve_document(copy.deepcopy(reloaded))
    controls = runtime['sections'][0]['items']
    assert controls[0]['name'] == 'shots_2'
    assert 'get_value("shots_2")' in controls[1]['bindings'][0]['script']
    assert authored_document(runtime)['sections'][0]['items'][1]['kind'] == 'reference'
    duplicate = EditorDocumentController(document).clone_subtree(linked)
    duplicate_runtime = resolver.resolve_document({'sections':[duplicate]})
    duplicate_controls = duplicate_runtime['sections'][0]['items']
    assert 'get_value("{0}")'.format(duplicate_controls[0]['name']) in duplicate_controls[1]['bindings'][0]['script']
    updated = copy.deepcopy(root)
    updated['items'][1]['ui']['label'] = 'Updated'
    publish_presets([{'id':'leo','root':updated}],remote,'studio','0+Media')
    SyncService(resolver.registry).check('studio',True)
    assert resolver.resolve(linked['items'][1])['ui']['label'] != 'Updated'
    assert PresetResolver(resolver.registry).resolve(linked['items'][1])['ui']['label'] == 'Updated'


def test_readable_files_manual_edit_move_and_reference_identity(tmp_path):
    import json
    root, remote, resolver = fixture(tmp_path)
    folder = tmp_path / 'remote'
    assert json.loads((folder / MANIFEST).read_text()) == {'schema': 1, 'id': 'studio', 'name': '0+Media'}
    path = folder / 'All' / 'Project Pipeline' / 'Leo.json'
    assert path.is_file()
    raw = json.loads(path.read_text())
    assert 'dcc' not in raw and 'category' not in raw
    ref = resolver.create_reference('studio', 'leo', 'open')
    raw['root']['items'][1]['ui']['label'] = 'Edited directly'
    moved = folder / 'Maya' / 'Pipeline' / 'Review' / 'Renamed.json'
    moved.parent.mkdir(parents=True)
    moved.write_text(json.dumps(raw))
    path.unlink()
    files_before = sorted(str(p.relative_to(folder)) for p in folder.rglob('*'))
    service = SyncService(resolver.registry)
    assert service.check('studio')['state'] == 'update_available'
    assert service.check('studio', True)['state'] == 'up_to_date'
    assert sorted(str(p.relative_to(folder)) for p in folder.rglob('*')) == files_before
    current = PresetResolver(resolver.registry)
    assert current.resolve(ref)['ui']['label'] == 'Edited directly'
    assert resolver.resolve(ref)['ui']['label'] != 'Edited directly'
    definition = current.packages['studio']['presets'][0]
    assert definition['dcc'] == 'maya' and definition['category'] == 'Pipeline/Review'
    moved.unlink()
    assert service.check('studio', True)['state'] == 'up_to_date'
    assert service.installed('studio')['presets'] == []


def test_duplicate_ids_and_incomplete_publish_keep_cache(tmp_path):
    import shutil
    root, remote, resolver = fixture(tmp_path)
    folder = tmp_path / 'remote'
    service = SyncService(resolver.registry)
    before = service.installed('studio')['manifest']
    shutil.copyfile(str(folder / 'All/Project Pipeline/Leo.json'), str(folder / 'All/Project Pipeline/Duplicate.json'))
    assert service.check('studio', True)['state'] == 'invalid_source'
    assert service.installed('studio')['manifest'] == before
    (folder / 'All/Project Pipeline/Duplicate.json').unlink()
    (folder / '.publish-interrupted').mkdir()
    assert service.check('studio', True)['state'] == 'invalid_source'
    assert service.installed('studio')['manifest'] == before


def test_publication_rollback_and_same_label_preserves_existing_file(tmp_path, monkeypatch):
    import script_toolbox.core.preset_library as publisher
    root, remote, resolver = fixture(tmp_path)
    folder = tmp_path / 'remote'
    original = (folder / 'All/Project Pipeline/Leo.json').read_bytes()
    publish_presets([{'id': 'aaa', 'label': 'Leo', 'category': 'Project Pipeline', 'root': root}],
                    remote, 'studio', 'ignored', merge=True)
    assert (folder / 'All/Project Pipeline/Leo.json').read_bytes() == original
    assert (folder / 'All/Project Pipeline/Leo-aaa.json').is_file()
    before = load_package(remote)['manifest']
    replace = publisher._replace_file
    failed = []
    def fail_once(src, dest):
        if dest.endswith('library.json') and not failed:
            failed.append(True)
            raise IOError('fixture: write interrupted')
        return replace(src, dest)
    monkeypatch.setattr(publisher, '_replace_file', fail_once)
    with pytest.raises(IOError):
        publish_presets([{'id': 'new', 'label': 'New', 'root': root}], remote, 'studio', 'Studio')
    assert load_package(remote)['manifest'] == before
    assert not list(folder.glob('.publish-*'))


@pytest.mark.parametrize('category', ['../Outside', 'Tools/CON', 'Tools/Bad:Name', '/Tools'])
def test_invalid_category_does_not_write_library(tmp_path, category):
    root, remote, resolver = fixture(tmp_path)
    before = load_package(remote)['manifest']
    with pytest.raises(ValueError):
        publish_presets([{'id': 'bad', 'category': category, 'root': root}], remote, 'studio', 'Studio', merge=True)
    assert load_package(remote)['manifest'] == before


def test_old_manifest_is_not_supported(tmp_path):
    import json
    folder = tmp_path / 'old'
    folder.mkdir()
    (folder / 'toolbox-source.json').write_text(json.dumps({'schema': 1, 'id': 'old', 'name': 'Old', 'revision': 1, 'presets': []}))
    with pytest.raises(IOError):
        load_package(str(folder))


def test_nonempty_folder_cannot_be_overwritten_as_new_library(tmp_path):
    folder = tmp_path / 'unrelated'
    folder.mkdir()
    original = folder / 'notes.json'
    original.write_text('user data')
    with pytest.raises(ValueError, match='empty folder'):
        publish_presets([], str(folder), 'studio', 'Studio')
    assert original.read_text() == 'user data'
    assert not (folder / MANIFEST).exists()


def test_failed_rollback_retains_backup_and_blocks_sync(tmp_path, monkeypatch):
    import script_toolbox.core.preset_library as publisher
    root, remote, resolver = fixture(tmp_path)
    folder = tmp_path / 'remote'
    before = SyncService(resolver.registry).installed('studio')['manifest']
    replace = publisher._replace_file
    def fail(src, dest):
        if dest.endswith('library.json') or 'backup' in src:
            raise IOError('fixture: unavailable disk')
        return replace(src, dest)
    monkeypatch.setattr(publisher, '_replace_file', fail)
    with pytest.raises(ValueError, match='rollback failed'):
        publish_presets([{'id': 'leo', 'label': 'Leo', 'category': 'Project Pipeline', 'root': root}], remote, 'studio', 'Studio')
    stages = list(folder.glob('.publish-*'))
    assert len(stages) == 1
    assert (stages[0] / 'backup/All/Project Pipeline/Leo.json').is_file()
    service = SyncService(resolver.registry)
    assert service.check('studio', True)['state'] == 'invalid_source'
    assert service.installed('studio')['manifest'] == before
