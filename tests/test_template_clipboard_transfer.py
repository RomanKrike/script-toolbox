# -*- coding: utf-8 -*-

import io
import os

import pytest

from script_toolbox.constants import CONFIG_VERSION
from script_toolbox.core import config
from script_toolbox.core.config_schema import ConfigSchemaError
from script_toolbox.core.config_schema import UnsupportedOldConfigVersionError


_FIXTURE_PATH = os.path.join(
    os.path.dirname(__file__),
    "fixtures",
    "current_v21_full.json"
)


def _read_text(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def _document(name=u"Template"):
    document = config.deserialize_config(
        _read_text(_FIXTURE_PATH)
    )
    document["sections"][0]["ui"]["label"] = name
    document["sections"][0]["items"][1]["bindings"][0]["script"] = (
        u"line_one = 'Юникод'\n"
        u"line_two = 'clipboard round trip'"
    )
    return document


def test_config_text_codec_round_trip_preserves_unicode_and_multiline_script():
    source = _document(u"Папка — Template")

    json_text = config.serialize_config(source)
    restored = config.deserialize_config(json_text)

    assert u"Папка — Template" in json_text
    assert u"Юникод" in json_text
    assert restored == source
    assert restored["sections"][0]["items"][1]["bindings"][0]["script"] == (
        u"line_one = 'Юникод'\n"
        u"line_two = 'clipboard round trip'"
    )


def test_file_export_and_clipboard_serializer_are_exactly_equivalent(tmp_path):
    source = _document(u"Round Trip")
    path = str(tmp_path / "template.json")

    config.export_config(source, path)

    assert _read_text(path) == config.serialize_config(source)
    assert config.import_config(path) == config.deserialize_config(
        config.serialize_config(source)
    )


def test_deserialize_transfer_accepts_full_template():
    source = _document(u"Transfer Template")

    transfer_kind, restored = config.deserialize_transfer(
        config.serialize_config(source)
    )

    assert transfer_kind == "config"
    assert restored == source


def test_deserialize_transfer_accepts_single_button_item():
    raw = u'''{
      "kind": "button",
      "id": "button_render_selected_write",
      "name": "render_selected_write",
      "ui": {
        "label": "Render Selected Write"
      },
      "props": {
        "icon_path": "stsolar:play.svg",
        "icon_size": 18,
        "icon_only": false
      },
      "bindings": [
        {
          "id": "render_selected_write_click",
          "event": "click",
          "handler": "script",
          "language": "python",
          "script": "import nuke\\nimport nukescripts\\n\\nwrites = [node for node in nuke.selectedNodes() if node.Class() == 'Write']\\n\\nif not writes:\\n    nuke.message('Select a Write node.')\\nelse:\\n    nukescripts.showRenderDialog(writes)",
          "label": "",
          "mouse_button": "left",
          "modifiers": [],
          "modifier_policy": "exact"
        }
      ]
    }'''

    transfer_kind, item = config.deserialize_transfer(raw)

    assert transfer_kind == "item"
    assert item["kind"] == "button"
    assert item["id"] == "button_render_selected_write"
    assert item["name"] == "render_selected_write"
    assert item["ui"]["label"] == "Render Selected Write"
    assert item["props"]["icon_path"] == "stsolar:play.svg"
    assert item["props"]["icon_size"] == 18
    assert item["props"]["icon_only"] is False
    assert "nukescripts.showRenderDialog(writes)" in item["bindings"][0]["script"]


def test_deserialize_rejects_non_json():
    with pytest.raises(ValueError):
        config.deserialize_config(u"this is not json")

    with pytest.raises(ValueError):
        config.deserialize_transfer(u"this is not json")


def test_deserialize_rejects_json_that_is_not_a_template():
    with pytest.raises(ConfigSchemaError):
        config.deserialize_config(u'["not", "a", "template"]')

    with pytest.raises(ConfigSchemaError):
        config.deserialize_config(u'{"version": %d}' % CONFIG_VERSION)

    with pytest.raises(ConfigSchemaError):
        config.deserialize_transfer(u'["not", "a", "transfer"]')

    with pytest.raises(ConfigSchemaError):
        config.deserialize_transfer(u'{"name": "missing_kind"}')


def test_clipboard_codec_and_file_import_reject_old_schema_the_same_way(tmp_path):
    old_json = u'{"version": %d, "sections": []}' % (CONFIG_VERSION - 1)

    with pytest.raises(UnsupportedOldConfigVersionError):
        config.deserialize_config(old_json)

    with pytest.raises(UnsupportedOldConfigVersionError):
        config.deserialize_transfer(old_json)

    path = str(tmp_path / "old.json")
    with io.open(path, "w", encoding="utf-8") as handle:
        handle.write(old_json)

    with pytest.warns(RuntimeWarning):
        with pytest.raises(UnsupportedOldConfigVersionError):
            config.import_config(path)
