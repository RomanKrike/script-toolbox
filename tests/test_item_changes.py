import copy

import pytest

from script_toolbox.core.item_changes import Item, resolve_item, update_item
from script_toolbox.model.items import create_item


def test_complete_candidate_is_atomic_and_reports_normalized_changes():
    item = create_item("integer", {"props": {"min": 0, "max": 100, "value": 50}})
    before = copy.deepcopy(item)
    props = item["props"]
    with pytest.raises(ValueError):
        update_item(item, {"label": "Changed", "value": "bad"})
    assert item == before
    change = update_item(item, {"max": 20, "label": "Changed"})
    assert item["props"]["value"] == 20
    assert change.before["props.value"] == 50
    assert change.after["props.max"] == 20
    assert item["props"] is props  # Render callbacks may hold this mapping.
    assert not update_item(item, {"value": 20}).changed


def test_properties_unknown_names_readonly_and_ui_namespaces():
    image = create_item("image")
    for field in ("sorce", "value", "kind", "name", "items"):
        with pytest.raises(ValueError):
            update_item(image, {field: "wrong"})
    update_item(image, {"width": 300, "ui.width": 150})
    assert image["props"]["width"] == 300
    assert image["ui"]["width"] == 150
    menu = create_item("menu")
    update_item(menu, {"items": ["a", "b"], "value": "b"})
    assert menu["props"]["value"] == "b"
    update_item(menu, {"items": ["c"]})
    assert menu["props"]["value"] == "c"


def test_script_owned_toggle_and_referenced_definitions():
    item = create_item("toggle_button", {"props": {"state_source": "script"}})
    with pytest.raises(ValueError):
        update_item(item, {"value": True})
    update_item(item, {"state_source": "internal", "value": True})
    assert item["props"]["value"] is True
    item["_preset_reference"] = {"id": "test"}
    with pytest.raises(ValueError):
        update_item(item, {"label": "Changed"})
    update_item(item, {"value": False})


def test_handle_identity_lifetime_and_copy_on_read():
    class Owner(object):
        pass
    owner = Owner()
    folder = create_item("folder", {"name": "tools"})
    owner.config = {"sections": [folder]}
    assert resolve_item(owner.config, "tools") is folder
    handle = Item(owner, "tools")
    folder["name"] = "renamed"
    assert handle.name == "renamed"
    with pytest.raises(AttributeError):
        handle.sorce = "bad"
    owner.config = copy.deepcopy(owner.config)
    with pytest.raises(RuntimeError):
        handle.set(label="Old document")
