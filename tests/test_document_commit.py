import copy
import pytest

from script_toolbox.core.document_commit import prepare_document_commit, DocumentMergeConflict
from script_toolbox.core.config_store import ConfigStore
from script_toolbox.model import create_item, normalize_document


def document():
    return normalize_document({"sections": [{"kind": "folder", "id": "root", "name": "root",
        "items": [create_item("string", {"id": "v", "name": "v", "props": {"value": "old"}})]}]})


def test_merge_preserves_runtime_value_and_editor_label():
    base = document()
    staged, current = copy.deepcopy(base), copy.deepcopy(base)
    staged["sections"][0]["items"][0]["ui"]["label"] = "Edited"
    current["sections"][0]["items"][0]["props"]["value"] = "new"
    result = prepare_document_commit(base, staged, current)
    assert result["sections"][0]["items"][0]["ui"]["label"] == "Edited"
    assert result["sections"][0]["items"][0]["props"]["value"] == "new"
    assert base["sections"][0]["items"][0]["props"]["value"] == "old"


def test_merge_rejects_competing_values():
    base = document()
    staged, current = copy.deepcopy(base), copy.deepcopy(base)
    staged["sections"][0]["items"][0]["props"]["value"] = "editor"
    current["sections"][0]["items"][0]["props"]["value"] = "runtime"
    with pytest.raises(DocumentMergeConflict, match="props/value"):
        prepare_document_commit(base, staged, current)


def test_merge_editor_addition_with_runtime_value_change():
    base = document()
    staged, current = copy.deepcopy(base), copy.deepcopy(base)
    staged["sections"][0]["items"].append(create_item("string", {"id": "added", "name": "added"}))
    current["sections"][0]["items"][0]["props"]["value"] = "new"
    items = prepare_document_commit(base, staged, current)["sections"][0]["items"]
    assert [item["id"] for item in items] == ["v", "added"]
    assert items[0]["props"]["value"] == "new"


def test_merge_rejects_removal_of_concurrently_edited_item():
    base = document()
    staged, current = copy.deepcopy(base), copy.deepcopy(base)
    staged["sections"][0]["items"] = []
    current["sections"][0]["items"][0]["props"]["value"] = "new"
    with pytest.raises(DocumentMergeConflict):
        prepare_document_commit(base, staged, current)


def test_failed_candidate_keeps_store_snapshot_and_dirty_state():
    original = document()
    def fail(*args, **kwargs):
        raise OSError("disk full")
    store = ConfigStore(original, writer=fail)
    store.mark_dirty()
    with pytest.raises(OSError):
        store.commit_candidate(copy.deepcopy(original))
    assert store.document is original
    assert store.dirty
    assert store.write_count == 0


def test_reordered_items_merge_by_id_instead_of_list_position():
    base = document()
    base['sections'][0]['items'].append(create_item('string', {'id':'other', 'name':'other'}))
    staged, current = copy.deepcopy(base), copy.deepcopy(base)
    staged['sections'][0]['items'].reverse()
    current['sections'][0]['items'][0]['props']['value'] = 'fresh'
    items = prepare_document_commit(base, staged, current)['sections'][0]['items']
    assert [item['id'] for item in items] == ['other', 'v']
    assert items[1]['props']['value'] == 'fresh'
