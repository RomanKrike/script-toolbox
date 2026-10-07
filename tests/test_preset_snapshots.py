from script_toolbox.core import preset_references as references
from script_toolbox.model import create_item


class Registry(object):
    def __init__(self, root):
        self.root = root
        self.entries = [{'id':'studio', 'remote_path':'fixture', 'enabled':True}]

    def sources(self):
        return list(self.entries)

    def cache_path(self, source_id):
        return str(self.root / source_id)


def package():
    root = create_item('folder', {'id':'root', 'name':'root'})
    root['items'] = [create_item('string', {'id':'v', 'name':'v'})]
    return {'presets':[{'id':'p', 'root':root}]}


def test_indexed_lookup_isolated_from_callers_and_does_not_walk(monkeypatch, tmp_path):
    registry = Registry(tmp_path)
    resolver = references.PresetResolver(registry, packages={'studio':package()})
    def fail(*args):
        raise AssertionError('lookup traversed the package')
    monkeypatch.setattr(references, 'iter_targets', fail)
    value = resolver.target('studio', 'p', 'v')
    value['props']['value'] = 'changed'
    assert resolver.target('studio', 'p', 'v')['props']['value'] == ''


def test_invalid_update_retains_only_matching_source_snapshot(monkeypatch, tmp_path):
    registry = Registry(tmp_path)
    previous = references.PresetResolver(registry, packages={'studio':package()})
    monkeypatch.setattr(references.SyncService, 'installed', lambda *args: None)
    current = references.load_preset_snapshot(registry, previous)
    assert current.target('studio', 'p', 'v')['id'] == 'v'
    registry.entries = [dict(registry.entries[0], remote_path='another-source')]
    assert not references.load_preset_snapshot(registry, previous).packages
    assert previous.target('studio', 'p', 'v')['id'] == 'v'


def test_loading_resolver_does_not_mutate_authored_references(tmp_path):
    registry = Registry(tmp_path)
    resolver = references.PresetResolver(registry, packages={})
    resolver.loading = True
    item = create_item('reference', {'props':{'source':'studio', 'preset':'p',
        'parameter':'v', 'target_kind':'string'}})
    document = {'sections':[create_item('folder', {'items':[item]})]}
    before = references.authored_document(document)
    assert resolver.resolve_document(document) == before


def test_changed_cache_pointer_marks_snapshot_stale(monkeypatch, tmp_path):
    registry = Registry(tmp_path)
    folder = tmp_path / 'studio'
    folder.mkdir()
    pointer = folder / 'active.json'
    pointer.write_text('{}')
    def installed(*args):
        pointer.write_text('{"current":"changed"}')
        return package()
    monkeypatch.setattr(references.SyncService, 'installed', installed)
    assert references.load_preset_snapshot(registry).cache_changed
