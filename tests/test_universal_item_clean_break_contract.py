# -*- coding: utf-8 -*-

import os


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


def _path(*parts):
    return os.path.join(ROOT, *parts)


def _source(*parts):
    with open(_path(*parts), "r") as handle:
        return handle.read()


def test_runtime_section_routing_has_no_folder_kind_switch():
    source = _source(
        "scripts", "script_toolbox", "ui", "runtime.py"
    )

    assert 'get("kind") == "folder"' not in source
    assert 'get("kind") != "folder"' not in source
    assert "ITEM_TYPES.get" in source
    assert "build_runtime_widget" in source


def test_clean_break_has_no_migration_registry_or_v20_fixtures():
    source = _source(
        "scripts", "script_toolbox", "core", "config_schema.py"
    )

    assert "MIGRATIONS" not in source
    assert "MissingMigrationStepError" not in source
    assert "InvalidMigrationResultError" not in source
    assert "MigrationValidationError" not in source

    assert not os.path.exists(_path(
        "tests", "test_config_migrations.py"
    ))
    assert not os.path.exists(_path(
        "tests", "fixtures", "current_v20_full.json"
    ))
    assert not os.path.exists(_path(
        "tests", "fixtures", "golden_v20_current.json"
    ))


def test_item_inspector_does_not_persist_legacy_callbacks():
    for parts in (
        ("scripts", "script_toolbox", "ui", "properties", "basic.py"),
        ("scripts", "script_toolbox", "ui", "properties", "separator.py"),
        ("scripts", "script_toolbox", "ui", "properties", "base.py"),
    ):
        source = _source(*parts)
        assert '["callbacks"]' not in source
        assert ".get(\"callbacks\"" not in source


def test_current_schema_is_v21_only_and_documented_as_clean_break():
    source = _source(
        "scripts", "script_toolbox", "core", "config_schema.py"
    )
    docs = _source("docs", "ARCHITECTURE.md")

    assert "historical migrations are unsupported" in source
    assert "Schema **21** is the single supported configuration contract" in docs
    assert "there is intentionally no schema 20 -> 21 migration" in docs
