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


def test_deserialize_rejects_non_json():
    with pytest.raises(ValueError):
        config.deserialize_config(u"this is not json")


def test_deserialize_rejects_json_that_is_not_a_template():
    with pytest.raises(ConfigSchemaError):
        config.deserialize_config(u'["not", "a", "template"]')

    with pytest.raises(ConfigSchemaError):
        config.deserialize_config(u'{"version": %d}' % CONFIG_VERSION)


def test_clipboard_codec_and_file_import_reject_old_schema_the_same_way(tmp_path):
    old_json = u'{"version": %d, "sections": []}' % (CONFIG_VERSION - 1)

    with pytest.raises(UnsupportedOldConfigVersionError):
        config.deserialize_config(old_json)

    path = str(tmp_path / "old.json")
    with io.open(path, "w", encoding="utf-8") as handle:
        handle.write(old_json)

    with pytest.warns(RuntimeWarning):
        with pytest.raises(UnsupportedOldConfigVersionError):
            config.import_config(path)
