# -*- coding: utf-8 -*-

import copy
import io
import json

import pytest

from script_toolbox.constants import CONFIG_VERSION
from script_toolbox.core import config
from script_toolbox.core.config_schema import ConfigSchemaError
from script_toolbox.core.config_schema import UnsupportedConfigVersionError
from script_toolbox.core.config_schema import detect_config_version
from script_toolbox.core.config_schema import validate_document_schema


def test_schema_20_is_the_only_supported_config_schema():
    assert CONFIG_VERSION == 20

    source = {
        "version": CONFIG_VERSION,
        "sections": [],
    }
    original = copy.deepcopy(source)
    prepared = validate_document_schema(source)

    assert prepared == original
    assert prepared is not source
    assert detect_config_version(prepared) == CONFIG_VERSION


def test_new_empty_config_gets_current_schema():
    prepared = validate_document_schema({})

    assert prepared == {
        "version": CONFIG_VERSION,
        "sections": [],
    }


def test_versionless_nonempty_config_is_rejected():
    with pytest.raises(UnsupportedConfigVersionError):
        validate_document_schema({"sections": []})


def test_older_schema_is_rejected():
    with pytest.raises(UnsupportedConfigVersionError):
        validate_document_schema({
            "version": CONFIG_VERSION - 1,
            "sections": [],
        })


def test_future_schema_is_rejected():
    with pytest.raises(UnsupportedConfigVersionError):
        validate_document_schema({
            "version": CONFIG_VERSION + 1,
            "sections": [],
        })


def test_invalid_schema_version_is_rejected():
    with pytest.raises(ConfigSchemaError):
        validate_document_schema({
            "version": "not-a-version",
            "sections": [],
        })


def test_load_config_rejects_old_schema_without_overwriting_file(tmp_path):
    path = str(tmp_path / "toolbox.json")
    source = {
        "version": CONFIG_VERSION - 1,
        "sections": [],
    }

    with io.open(path, "w", encoding="utf-8") as handle:
        json.dump(source, handle)

    with pytest.warns(RuntimeWarning):
        with pytest.raises(UnsupportedConfigVersionError):
            config.load_config(path=path)

    with io.open(path, "r", encoding="utf-8") as handle:
        assert json.load(handle) == source


def test_save_config_rejects_wrong_schema_before_writing(tmp_path):
    path = str(tmp_path / "toolbox.json")

    with pytest.raises(UnsupportedConfigVersionError):
        config.save_config(
            {
                "version": CONFIG_VERSION - 1,
                "sections": [],
            },
            path=path
        )

    assert not tmp_path.joinpath("toolbox.json").exists()
