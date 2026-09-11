# -*- coding: utf-8 -*-

import copy
import io
import json

import pytest

from script_toolbox.constants import CONFIG_VERSION
from script_toolbox.core import config
from script_toolbox.core.config_schema import ConfigSchemaError
from script_toolbox.core.config_schema import FutureConfigVersionError
from script_toolbox.core.config_schema import InvalidMigrationResultError
from script_toolbox.core.config_schema import MIGRATIONS
from script_toolbox.core.config_schema import MigrationValidationError
from script_toolbox.core.config_schema import MissingConfigVersionError
from script_toolbox.core.config_schema import MissingMigrationStepError
from script_toolbox.core.config_schema import UnsupportedOldConfigVersionError
from script_toolbox.core.config_schema import migrate_document_schema


def test_current_schema_is_validated_without_migration_and_copied():
    source = {"version": CONFIG_VERSION, "sections": []}
    result = migrate_document_schema(source)
    assert result == source
    assert result is not source


def test_migration_pipeline_applies_sequential_steps_without_mutating_source():
    source = {"version": 20, "sections": [], "value": 1}
    original = copy.deepcopy(source)

    def migrate_20_to_21(document):
        document["version"] = 21
        document["value"] += 1
        return document

    def migrate_21_to_22(document):
        document["version"] = 22
        document["value"] += 1
        return document

    result = migrate_document_schema(
        source,
        expected_version=22,
        migrations={20: migrate_20_to_21, 21: migrate_21_to_22}
    )

    assert source == original
    assert result["version"] == 22
    assert result["value"] == 3


def test_migration_pipeline_reports_version_failures():
    with pytest.raises(MissingConfigVersionError):
        migrate_document_schema({"sections": []})

    with pytest.raises(FutureConfigVersionError):
        migrate_document_schema({
            "version": CONFIG_VERSION + 1,
            "sections": [],
        })

    with pytest.raises(UnsupportedOldConfigVersionError):
        migrate_document_schema({
            "version": CONFIG_VERSION - 1,
            "sections": [],
        })

    def migrate_20_to_21(document):
        document["version"] = 21
        return document

    with pytest.raises(MissingMigrationStepError):
        migrate_document_schema(
            {"version": 20, "sections": []},
            expected_version=22,
            migrations={20: migrate_20_to_21}
        )

    def broken(document):
        document["version"] = 22
        return document

    with pytest.raises(InvalidMigrationResultError):
        migrate_document_schema(
            {"version": 20, "sections": []},
            expected_version=21,
            migrations={20: broken}
        )


def test_migration_validation_failure_is_explicit():
    def migrate_20_to_21(document):
        document["version"] = 21
        return document

    def reject(document, expected_version=None):
        raise ConfigSchemaError("invalid current document")

    with pytest.raises(MigrationValidationError):
        migrate_document_schema(
            {"version": 20, "sections": []},
            expected_version=21,
            migrations={20: migrate_20_to_21},
            validator=reject
        )


def test_load_migrates_in_memory_and_save_preserves_raw_backup(tmp_path, monkeypatch):
    previous = CONFIG_VERSION - 1

    def migrate_previous(document):
        document["version"] = CONFIG_VERSION
        return document

    monkeypatch.setitem(MIGRATIONS, previous, migrate_previous)
    path = str(tmp_path / "toolbox.json")
    original = {"version": previous, "sections": []}
    with io.open(path, "w", encoding="utf-8") as handle:
        json.dump(original, handle)

    loaded = config.load_config(path=path)
    assert loaded["version"] == CONFIG_VERSION
    with io.open(path, "r", encoding="utf-8") as handle:
        assert json.load(handle) == original

    config.save_config(loaded, path=path)
    with io.open(path, "r", encoding="utf-8") as handle:
        assert json.load(handle)["version"] == CONFIG_VERSION
    with io.open(config.backup_path(path, 1), "r", encoding="utf-8") as handle:
        assert json.load(handle) == original
