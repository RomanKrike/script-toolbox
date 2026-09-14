# Архитектура

Script Toolbox — модульный multi-DCC toolbox для Maya, Nuke и Houdini с общей моделью и core-слоем.

## Целевая совместимость

### Maya
- Maya 2015–2016 — Python 2.7, PySide / Qt 4
- Maya 2017–2024 — PySide2 / Qt 5
- Maya 2025+ — PySide6 / Qt 6
- Python и MEL для event scripts

### Nuke
- Nuke 12–15 — PySide2 / Qt 5
- Nuke 16+ — PySide6 / Qt 6
- Python для event scripts

### Houdini
- Houdini 19–20.x — PySide2 / Qt 5
- Houdini 20.5 Qt 6 builds — PySide6 / Qt 6
- Houdini 21 — PySide6 / Qt 6, отдельные Qt 5.15.2 builds через PySide2
- Houdini 22+ — PySide6 / Qt 6
- Python и HScript для event scripts

Общий UI не форкается по поколениям DCC. `qt_compat.py` выбирает PySide / PySide2 / PySide6 во время запуска, предпочитает binding, уже выбранный хостом, и предоставляет совместимую legacy-поверхность `QtGui`.

Исторические схемы конфигурации намеренно не поддерживаются, пока плагин активно развивается.

## Направление зависимостей

```text
model -> core -> hosts -> ui

ui/main_window -> ui/runtime -> core/values -> model
      |               |
      |               -> style
      |
      -> core/config -> core/config_schema
      -> core/user_paths -> hosts
      -> core/event_bindings -> core/executor
      -> compat -> hosts
                 -> qt_compat
```

`model` должен импортироваться без Maya и Qt. Host-specific API находится в `hosts/` и integration modules. Выбор Qt binding принадлежит `qt_compat.py`.

## Текущая схема конфигурации

Schema **21** — единственный поддерживаемый контракт.

```text
JSON read
  -> validate schema version 21
  -> normalize Item envelope и typed props
  -> runtime document
```

Непустой документ без `version`, старая schema и более новая schema отклоняются. Config layer не мигрирует и не down-convert исторические payloads. В частности, migration `20 -> 21` намеренно отсутствует.

## Универсальный Item

Каждый persisted Item использует один envelope:

```json
{
  "kind": "integer",
  "id": "integer_samples",
  "name": "samples",
  "ui": {
    "label": "Samples",
    "show_label": true,
    "tooltip": "",
    "width_mode": "auto",
    "width": 120,
    "stretch": 1,
    "alignment": "left",
    "height_mode": "auto",
    "height": 28,
    "vertical_stretch": 1
  },
  "props": {
    "value": 8,
    "min": 1,
    "max": 64,
    "step": 1
  },
  "bindings": []
}
```

Container добавляет только `items`. Presentation/layout state хранится в `ui`, type-specific данные — в `props`, event behavior — в `bindings`. Type-specific root keys не являются вторым форматом persistence.

`model/item_view.py` предоставляет `ItemDataView` — неперсистентный adapter для runtime и Inspector. Он маршрутизирует presentation keys в `ui`, а type-specific keys в `props`, не меняя serialized schema 21.

Identity contract:

- `id` — стабильный внутренний идентификатор;
- `name` — символический идентификатор для scripts/API;
- `ui.label` — только presentation text и не участвует в lookup.

Unknown `kind` отклоняется, а не преобразуется в другой тип.

## ItemTypeRegistry

`model/item_registry.py` — единая точка расширения. Новый тип описывается `ItemTypeDefinition`, а core-подсистемы читают metadata definition вместо параллельных списков `kind`.

Definition хранит:

- `kind`, `title`, `category`, `description`, `order`, `creatable`;
- typed `fields` для нормализации `props`;
- `events` и `internal_events`;
- semantic `capabilities` (`container`, `layout`, `has_value`, `state_toggle`, `resizable`, `field_widget` и т. д.);
- defaults и normalization hooks;
- `renderer_path` и `inspector_path` для lazy Qt-side resolution.

Built-in definitions находятся в `model/item_builtins.py`. Core routing больше не использует `_FACTORIES`, `EVENT_CAPABILITIES`, `LAYOUT_KINDS`, `CONTAINER_KINDS`, `STATE_TOGGLE_KINDS` или central property-editor map.

`ui/item_ui_bootstrap.py` generic: он проходит по `ITEM_TYPES`, разрешает UI paths и записывает renderer/inspector обратно в definition. `ui/runtime_renderers.py`, `ui/properties/registry.py`, bindings, values и palette используют ту же metadata.

### Добавление нового типа

Новый тип не должен требовать правки центральных dispatch tables. Например:

```python
from script_toolbox.model.fields import BoolField, PathField
from script_toolbox.model.item_registry import ItemTypeDefinition, register_item_type

register_item_type(ItemTypeDefinition(
    kind="video",
    title="Video",
    category="Display",
    fields={
        "source": PathField(default=""),
        "autoplay": BoolField(default=False),
    },
    events=("click", "double_click"),
    capabilities=("bindable", "resizable"),
    renderer_path=".video_item:render_video",
    inspector_path=".video_item:VideoPropertyEditor",
))
```

После регистрации model construction понимает `video`, Add Item palette получает entry из registry metadata, runtime и Inspector разрешаются из definition. Built-in `image` — production proof этого контракта. `tests/test_universal_item_extensibility.py` дополнительно проверяет тот же путь временным `video` Item.

## Container, bindings и values

Container semantics принадлежат definitions. Traversal, indexing, cloning, topology и reference rewriting используют capabilities и канонический `walk_items()`, а не tuple со списком container kinds.

`bindings` — единственный persisted/runtime event mechanism. Callback dictionaries и прямые script fields не являются вторым event API. Обычный `button` остаётся action-only; stateful behavior принадлежит `toggle_button` и `toggle_icon` через handler `state_toggle`.

Toggle Button и Toggle Icon участвуют в generic value API только при `state_source == "internal"`. Script-driven toggle не получает искусственный `props.value` через `store_value()`.

Numeric scalar/vector values нормализуются definition hooks. Field сохраняет прежнюю runtime semantics: scalar -> text, list/tuple -> list of text, single-value field берёт первый элемент списка.

## Editor и palette

`EditorDocumentController` владеет staged document, identity cache, clone/reference operations и topology и не зависит от Qt.

Активный Interface Editor собирается через `ui/editor_document_adapter.py`. Add Item palette строится из `ITEM_TYPES.creatable()` в `ui/item_palette.py`; authoritative catalog находится в type metadata.

## UI composition

`ui/bootstrap.py` — composition root UI/runtime. `ui/__init__.py` остаётся маленьким public export surface:

```python
_RUNTIME = initialize_ui()
```

`initialize_ui()` идемпотентен в рамках одного module graph. При hot reload активный runtime registry переиспользуется, если runtime module не изменился; при reload `ui.runtime` создаётся новый registry.

UI binding конкретного типа принадлежит `ItemTypeDefinition`, а не bootstrap table. `ui/item_ui_bootstrap.py` разрешает `renderer_path` / `inspector_path` generic loop-ом.

## Runtime rendering

`RuntimeFolder.build_runtime_widget()` dispatch-ит через runtime renderer registry. Default registry строится из `definition.renderer` после generic UI binding resolution.

Runtime event filters подключают только events, объявленные definition, и dispatch-ят их через `bindings`.

Runtime value synchronization capability-driven. Обычные `has_value` Item регистрируют `RuntimeValueBinding`; специальный Field refresh определяется capability `field_widget`, а не `kind == "field"`.

## Пути пользовательской конфигурации

`core/user_paths.py` — единственный владелец runtime config/settings path resolution. Stable и Development используют одинаковые canonical user files.

Для Maya:

```text
<cmds.internalVar(userPrefDir=True)>/maya_script_toolbox.json
<cmds.internalVar(userPrefDir=True)>/script_toolbox_settings.json
```

## Сетевой transport

`core/http_transport.py` — единый low-level HTTP transport для updater и sharing. Он остаётся Qt/DCC-independent. Legacy Windows/Python 2 может использовать PowerShell/.NET fallback с TLS 1.2; callers получают единый `TransportError`-контракт.

## Compatibility policy

Compatibility shims допускаются только для реально внешних/importable API и не должны становиться независимыми реализациями. Новый production flow использует канонические registry/core APIs.

## Основные модули

```text
scripts/script_toolbox/
  core/
    config.py
    config_schema.py
    editor_document.py
    event_bindings.py
    executor.py
    runtime_registry.py
    values.py

  model/
    bindings.py
    fields.py
    index.py
    item_builtins.py
    item_registry.py
    item_view.py
    items.py
    layouts.py

  ui/
    bootstrap.py
    item_palette.py
    item_ui_bootstrap.py
    image_item.py
    runtime.py
    runtime_renderers.py
    runtime_value_sync.py
    main_window.py

    properties/
      base.py
      registry.py
      folder.py
      row.py
      column.py
      basic.py
      field.py
      button.py
      toggle_button.py
      icon.py
      toggle_icon.py
      text.py
      separator.py
```

## Правила

- Никаких circular imports.
- Никакого DCC UI/API-кода в `model`.
- Никакого JSON file I/O в `ui`.
- Поддерживается только current config schema.
- Persisted Item использует только schema 21 envelope; type-specific root keys не добавляются как compatibility layer.
- Unknown item kind нельзя silently convert в другой kind.
- `ui.label` нельзя использовать как identity.
- Event behavior сохраняется только в `bindings`.
- Новый Item type регистрируется через `ItemTypeDefinition`; core, palette, events, runtime и Inspector routing выводятся из metadata без central kind tables.
- Structural recursion использует container capabilities.
- Qt compatibility принадлежит `qt_compat.py`.
- UI/runtime composition ordering принадлежит `ui/bootstrap.py`.
- Source остаётся Python 2.7 compatible, пока поддержка Maya 2015 / Nuke 12 не будет намеренно прекращена.
