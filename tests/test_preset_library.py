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
