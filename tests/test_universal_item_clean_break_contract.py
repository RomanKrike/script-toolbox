# -*- coding: utf-8 -*-

import json
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


def _raw_items(document):
    stack = list(document.get("sections", []) or [])
    while stack:
        item = stack.pop(0)
        yield item
        stack[0:0] = list(item.get("items", []) or [])


def test_runtime_section_routing_uses_sectionspec_not_folder_schema_name():
    source = _source(
        "scripts", "script_toolbox", "ui", "runtime.py"
    )

    assert 'get("kind") == "folder"' not in source
    assert 'get("kind") != "folder"' not in source
    assert "ITEM_TYPES.get" in source
    assert "build_runtime_widget" in source
    assert "definition.section_mode(" in source
    assert 'definition.fields.get("folder_type")' not in source
    assert '_props(item).get("folder_type")' not in source


def test_generic_layout_metadata_has_no_magic_row_column_schema_inference():
    registry_source = _source(
        "scripts", "script_toolbox", "model", "item_registry.py"
    )
    adapter_source = _source(
        "scripts", "script_toolbox", "ui", "properties", "layout_adapter.py"
    )

    assert "class LayoutSpec" in registry_source
    assert "return spec.axis" in registry_source
    assert '"horizontal_distribution" in self.fields' not in registry_source
    assert '"vertical_distribution" in self.fields' not in registry_source

    for magic_name in (
        "horizontal_distribution",
        "vertical_distribution",
        "horizontal_alignment",
        "vertical_alignment",
        "equal_widths",
    ):
        assert magic_name not in adapter_source
    assert "parent_definition.layout_spec" in adapter_source
    assert "spec.distribution_field" in adapter_source
    assert "spec.cross_alignment_field" in adapter_source


def test_clean_break_has_no_migration_surface_or_v20_fixtures():
    schema_source = _source(
        "scripts", "script_toolbox", "core", "config_schema.py"
    )
    config_source = _source(
        "scripts", "script_toolbox", "core", "config.py"
    )

    for forbidden in (
        "MIGRATIONS",
        "migrate_document_schema",
        "MissingMigrationStepError",
        "InvalidMigrationResultError",
        "MigrationValidationError",
    ):
        assert forbidden not in schema_source
        assert forbidden not in config_source

    assert "validate_document_schema" in config_source
    assert not os.path.exists(_path(
        "tests", "test_config_migrations.py"
    ))
    assert not os.path.exists(_path(
        "tests", "fixtures", "current_v20_full.json"
    ))
    assert not os.path.exists(_path(
        "tests", "fixtures", "golden_v20_current.json"
    ))


def test_current_v21_fixtures_use_canonical_item_envelope():
    required = set((
        "kind",
        "id",
        "name",
        "ui",
        "props",
        "bindings",
    ))

    for fixture in (
        "current_v21_full.json",
        "golden_v21_current.json",
    ):
        with open(_path("tests", "fixtures", fixture), "r") as handle:
            document = json.load(handle)

        assert document["version"] == 21
        for item in _raw_items(document):
            assert required.issubset(set(item)), (fixture, item.get("id"))
            assert isinstance(item["ui"], dict)
            assert isinstance(item["props"], dict)
            assert isinstance(item["bindings"], list)
            if "items" in item:
                assert isinstance(item["items"], list)


def test_item_inspector_routes_props_through_schema_and_has_no_callbacks():
    base_source = _source(
        "scripts", "script_toolbox", "ui", "properties", "base.py"
    )
    assert "normalize_item_props(self.item)" in base_source

    for parts in (
        ("scripts", "script_toolbox", "ui", "properties", "basic.py"),
        ("scripts", "script_toolbox", "ui", "properties", "separator.py"),
        ("scripts", "script_toolbox", "ui", "properties", "base.py"),
    ):
        source = _source(*parts)
        assert '["callbacks"]' not in source
        assert ".get(\"callbacks\"" not in source


def test_reference_rewrite_uses_only_props_and_bindings_item_scripts():
    source = _source(
        "scripts", "script_toolbox", "core", "references.py"
    )

    assert "python_prop_script_keys" in source
    assert 'item.get("props"' in source
    assert 'item.get("callbacks")' not in source
    assert "schema-17" not in source.lower()
    assert "click_script" not in source
    assert "on_change_script" not in source


def test_item_source_has_no_legacy_folder_traversal_or_type_constant():
    legacy_traversal = "include_" + "folders"
    legacy_constant = "FOLDER_" + "TYPES"
    offenders = []

    scripts_root = _path("scripts")
    for directory, subdirectories, filenames in os.walk(scripts_root):
        subdirectories[:] = [
            name
            for name in subdirectories
            if name != "__pycache__"
        ]
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            path = os.path.join(directory, filename)
            with open(path, "r") as handle:
                source = handle.read()
            if legacy_traversal in source or legacy_constant in source:
                offenders.append(os.path.relpath(path, ROOT))

    assert offenders == []


def test_current_schema_is_v21_only_and_documented_as_clean_break():
    docs = _source("docs", "ARCHITECTURE.md")
    docs_ru = _source("docs", "ARCHITECTURE.ru.md")

    assert "Schema **21** is the single supported configuration contract" in docs
    assert "there is intentionally no schema 20 -> 21 migration" in docs
    assert "ItemDataView" not in docs
    assert "ItemDataView" not in docs_ru
    assert "item_view.py" not in docs
    assert "item_view.py" not in docs_ru
