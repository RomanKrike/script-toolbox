# -*- coding: utf-8 -*-

import copy
import io
import json

import pytest

from script_toolbox.constants import CONFIG_VERSION
from script_toolbox.core import config
from script_toolbox.core.migrations import ConfigMigrationError
from script_toolbox.core.migrations import LEGACY_CONFIG_VERSION
from script_toolbox.core.migrations import UnsupportedConfigVersionError
from script_toolbox.core.migrations import detect_config_version
from script_toolbox.core.migrations import migrate_document


def test_schema_15_is_legacy_migration_baseline():
    assert LEGACY_CONFIG_VERSION == 15
    assert CONFIG_VERSION == 17


def test_versionless_document_is_treated_as_schema_15():
    document = {
        "sections": [],
    }

    assert detect_config_version(document) == 15


def test_schema_15_migrates_to_current_without_mutating_source():
    source = {
        "version": 15,
        "sections": [
            {
                "kind": "folder",
                "name": "tools",
                "label": "Tools",
                "items": [
                    {
                        "kind": "button",
                        "name": "freeze",
                        "label": "Freeze",
                        "click_script": "print('freeze')",
                    }
                ],
            }
        ],
    }
    original = copy.deepcopy(source)

    migrated = migrate_document(source)

    assert source == original
    assert migrated["version"] == CONFIG_VERSION
    assert migrated["sections"][0]["name"] == "tools"
    assert migrated["sections"][0]["items"][0]["click_script"] == (
        "print('freeze')"
    )
    assert migrated["sections"][0]["items"][0]["callbacks"] == {}


def test_versionless_legacy_document_migrates_to_current():
    migrated = migrate_document(
        {
            "folders": [
                {
                    "name": "legacy_tools",
                }
            ]
        }
    )

    assert migrated["version"] == CONFIG_VERSION
    assert migrated["folders"][0]["name"] == "legacy_tools"


def test_schema_16_on_change_migrates_to_callbacks():
    source = {
        "version": 16,
        "sections": [
            {
                "kind": "folder",
                "name": "tools",
                "items": [
                    {
                        "kind": "integer",
                        "name": "samples",
                        "on_change_script": "print(value)",
                    }
                ],
            }
        ],
    }

    migrated = migrate_document(source)
    item = migrated["sections"][0]["items"][0]

    assert migrated["version"] == 17
    assert item["callbacks"] == {
        "on_change": "print(value)",
    }
    assert "on_change_script" not in item


def test_current_schema_is_returned_as_independent_copy():
    source = {
        "version": CONFIG_VERSION,
        "sections": [],
    }

    migrated = migrate_document(source)
    migrated["sections"].append({"name": "new"})

    assert source["sections"] == []


def test_future_schema_is_rejected():
    with pytest.raises(UnsupportedConfigVersionError):
        migrate_document(
            {
                "version": CONFIG_VERSION + 1,
                "sections": [],
            }
        )


def test_invalid_schema_version_is_rejected():
    with pytest.raises(ConfigMigrationError):
        migrate_document(
            {
                "version": "not-a-version",
                "sections": [],
            }
        )


def test_no_migration_path_is_rejected():
    with pytest.raises(ConfigMigrationError):
        migrate_document(
            {
                "version": LEGACY_CONFIG_VERSION - 1,
                "sections": [],
            }
        )


def test_load_config_migrates_schema_15(tmp_path):
    path = str(tmp_path / "toolbox.json")

    with io.open(
        path,
        "w",
        encoding="utf-8"
    ) as handle:
        json.dump(
            {
                "version": 15,
                "sections": [
                    {
                        "kind": "folder",
                        "name": "legacy_tools",
                        "items": [],
                    }
                ],
            },
            handle
        )

    document = config.load_config(path=path)

    assert document["version"] == CONFIG_VERSION
    assert document["sections"][0]["name"] == "legacy_tools"
    assert document["sections"][0]["items"] == []


def test_load_config_does_not_fallback_for_future_schema(tmp_path):
    path = str(tmp_path / "toolbox.json")
    source = {
        "version": CONFIG_VERSION + 1,
        "sections": [
            {
                "kind": "folder",
                "name": "future_tools",
                "items": [],
            }
        ],
    }

    with io.open(
        path,
        "w",
        encoding="utf-8"
    ) as handle:
        json.dump(
            source,
            handle
        )

    with pytest.warns(RuntimeWarning):
        with pytest.raises(UnsupportedConfigVersionError):
            config.load_config(path=path)

    with io.open(
        path,
        "r",
        encoding="utf-8"
    ) as handle:
        assert json.load(handle) == source


def test_save_config_rejects_future_schema_before_writing(tmp_path):
    path = str(tmp_path / "toolbox.json")

    with pytest.raises(UnsupportedConfigVersionError):
        config.save_config(
            {
                "version": CONFIG_VERSION + 1,
                "sections": [],
            },
            path=path
        )

    assert not tmp_path.joinpath("toolbox.json").exists()
