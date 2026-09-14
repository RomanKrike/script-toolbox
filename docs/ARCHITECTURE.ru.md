# Архитектура

Script Toolbox — модульный multi-DCC toolbox для Maya, Nuke и Houdini с общей model/core архитектурой.

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

`model` должен импортироваться без Maya и Qt. Host-specific API находится в `hosts/` и integration modules. Выбор Qt binding принадлежит `qt_compat.py`. Model/core не импортируют UI ради Item registration.

## Текущая схема конфигурации

Schema **21** — единственный поддерживаемый контракт.

```text
JSON read
  -> validate schema version 21
  -> normalize current Item envelopes и typed props
  -> runtime document
```

Непустой документ без `version`, старая schema и более новая schema отклоняются. Config layer не мигрирует и не down-convert исторические payloads. Migration `20 -> 21` намеренно отсутствует. Пустой mapping используется только для создания нового current-schema document.

## Универсальный Item

Каждый persisted и runtime Item использует один envelope:

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

Container добавляет только `items`. Presentation/layout state хранится в `ui`, type-specific данные — в `props`, event behavior — в `bindings`. Runtime и Inspector читают эти namespaces напрямую. Flat Item compatibility view и второго in-memory формата нет.

Identity contract:

- `id` — стабильный внутренний идентификатор;
- `name` — символический идентификатор для scripts/API;
- `ui.label` — только presentation text и не участвует в lookup.

Unknown `kind` отклоняется, а не преобразуется в другой тип. `kind` — единственный discriminator; параллельного `type` нет.

## ItemTypeRegistry

`model/item_registry.py` — authoritative extension point. Новый тип описывается `ItemTypeDefinition`, а общие подсистемы читают definition вместо параллельных списков `kind`.

Definition хранит:

- `kind`, `title`, `category`, `description`, `order`, `creatable`;
- typed `fields` для `props`;
- public `events` и `internal_events`;
- semantic `capabilities`, например `container`, `layout`, `section`, `has_value`, `state_toggle`, `resizable`, `field_widget`, `native_button`, `divider`;
- defaults для `ui` и bindings;
- optional `normalize_props` hook для cross-field invariants;
- `renderer_path` и `inspector_path` для lazy Qt-side resolution;
- после UI resolution — реальные `renderer` и `inspector` callables/classes.

`layout_axis` выводится из schema metadata layout-definition, поэтому generic editor/layout code не идентифицирует Row/Column по имени.

Core routing больше не использует `_FACTORIES`, `EVENT_CAPABILITIES`, `LAYOUT_KINDS`, `CONTAINER_KINDS`, `STATE_TOGGLE_KINDS`, central property-editor mapping, renderer switch или authored palette list.

Standard built-ins регистрируются `model/item_builtins.py`. Отдельно расширяемые built-ins находятся в `model/item_definitions/`; `Image` определён в `model/item_definitions/image.py` и включён через явный built-in bootstrap. Для нового built-in допустима одна запись в explicit bootstrap/import list.

`ui/item_ui_bootstrap.py` generic и re-entrant: он каждый раз проходит по текущему `ITEM_TYPES`, разрешает только ещё не разрешённые `renderer_path` / `inspector_path` и записывает callables обратно в definition. Поэтому тип может быть зарегистрирован как до, так и после первого UI bootstrap.

## Field schema

Model предоставляет декларативные `TextField`, `BoolField`, `IntField`, `FloatField`, `ChoiceField`, `ColorField`, `PathField` и `ListField`.

Field отвечает за:

- default;
- normalization;
- validation;
- numeric bounds, когда применимо;
- choices, когда применимо.

Сложные зависимости остаются на уровне `ItemTypeDefinition.normalize_props`:

```text
raw props
  -> per-field normalization
  -> ItemTypeDefinition.normalize_props
  -> normalized props
```

Так реализуются numeric vector invariants, Menu values, Field display semantics и state-toggle storage behavior.

## Как добавить новый Item type

Routing core менять не нужно.

Для built-in `video`:

1. добавить `model/item_definitions/video.py` с `ItemTypeDefinition`;
2. добавить renderer и специализированный Inspector;
3. включить `video_definition()` в explicit built-in bootstrap tuple;
4. добавить tests.

Пример:

```python
from script_toolbox.model.fields import BoolField, ChoiceField, PathField
from script_toolbox.model.item_registry import ItemTypeDefinition


def video_definition():
    return ItemTypeDefinition(
        kind="video",
        title="Video",
        category="Display",
        fields={
            "source": PathField(default=""),
            "autoplay": BoolField(default=False),
            "loop": BoolField(default=False),
            "fit": ChoiceField(
                ("contain", "cover", "stretch"),
                default="contain"
            ),
        },
        events=("click", "double_click"),
        capabilities=("bindable", "resizable"),
        renderer_path=".video_item:render_video",
        inspector_path=".video_item:VideoPropertyEditor",
    )
```

Правки не требуются в `bindings.py`, `layouts.py`, runtime dispatch, `properties/registry.py`, `interface_editor.py`, `item_palette.py` или document normalization.

Future/external code может вызвать `register_item_type()` напрямую и не менять built-in bootstrap. Registration поддерживается и после первого UI composition: следующий Inspector/UI binding lookup разрешит paths, а активный runtime renderer registry при следующем lookup синхронизирует отсутствующий renderer и применит generic event/value decorators. Уже открытая palette не refresh-ится магически; новый entry гарантированно появляется при следующем построении palette из `ITEM_TYPES.creatable()`.

Built-in `Image` — production proof этого контракта. Он определяет только `source`, `fit`, `width`, `height`, поддерживает `contain` / `cover` / `stretch`, объявляет `click` / `double_click` и поставляет renderer/Inspector через definition metadata.

`tests/test_universal_item_extensibility.py` дополнительно регистрирует временный module-based `video` уже после simulated UI bootstrap и проверяет path resolution, bindings, active runtime registry и auto-palette без правок core routing.

## Containers, bindings и values

Container semantics принадлежат definitions. Traversal, indexing, cloning, topology и reference rewriting используют capabilities и канонический `walk_items()`, а не tuple со списком container kinds.

Top-level sections выражаются capability `section`. `walk_items(document)` по умолчанию не возвращает section Items; `walk_items(document, include_sections=True)` включает их явно. Старого `include_folders` compatibility API нет.

Layout containers используют capability `layout`; generic editor rules запрещают layout владеть section без проверки конкретного имени kind.

`bindings` — единственный persisted/runtime event mechanism. Callback dictionaries и прямые script fields не являются вторым event API. Обычный `button` action-only. Stateful semantics определяются capability `state_toggle`, а button chrome — `native_button`.

Toggle Button и Toggle Icon участвуют в generic value API только при `state_source == "internal"`. Script-driven toggle не получает искусственный `props.value` через `store_value()`.

Numeric scalar/vector values нормализуются теми же definition hooks при construction и runtime writes. Field сохраняет runtime semantics: scalar -> text, list/tuple -> list of text, single-value field берёт первый элемент списка.

## Editor и palette

`EditorDocumentController` владеет staged document, identity cache, clone/reference operations и topology и не зависит от Qt.

Base Interface Editor использует registry для palette entries, type titles, container/section semantics и tree structure. `ui/layout_editor_adapter.py` содержит reusable capability-driven helpers и не поддерживает отдельный список Folder/Row/Column kinds.

Add Item palette строится из `ITEM_TYPES.creatable()` каждый раз при построении UI. Categories выводятся из metadata, поэтому новый category не требует правки editor source.

## UI composition

`ui/bootstrap.py` — composition root UI/runtime. `ui/__init__.py` остаётся маленьким public export surface:

```python
_RUNTIME = initialize_ui()
```

`initialize_ui()` идемпотентен в рамках одного module graph. При hot reload активный runtime registry переиспользуется, если runtime module не изменился; при reload `ui.runtime` создаётся новый registry.

UI binding конкретного типа принадлежит `ItemTypeDefinition`, а не bootstrap table. Re-entrant `ui/item_ui_bootstrap.py` разрешает UI paths для текущего состава registry, включая late registrations.

## Runtime rendering

`RuntimeFolder.build_runtime_widget()` dispatch-ит через runtime renderer registry. Default registry строится из `definition.renderer` после generic UI binding resolution.

Активный registry также синхронизируется с `ITEM_TYPES` при lookup. Если definition зарегистрирован поздно и имеет renderer path, UI binding resolution загружает callable, registry добавляет отсутствующий kind, а generic event/value decorators применяются идемпотентно. Центрального kind -> renderer switch нет.

Runtime renderer получает raw universal Item envelope и явно читает `ui` / `props`.

Runtime event filters подключают только events, объявленные definition, и dispatch-ят их через `bindings`.

Runtime value synchronization capability-driven. Обычные `has_value` Item регистрируют `RuntimeValueBinding`; специальный Field refresh определяется capability `field_widget`, а не `kind == "field"`.

Section mode validation также следует schema metadata: допустимые `folder_type` значения и default принадлежат `ChoiceField` Folder definition, а runtime не хранит второй validation list.

## Пути пользовательской конфигурации

`core/user_paths.py` — единственный владелец runtime config/settings path resolution. Stable и Development используют одинаковые canonical user files.

Для Maya:

```text
<cmds.internalVar(userPrefDir=True)>/maya_script_toolbox.json
<cmds.internalVar(userPrefDir=True)>/script_toolbox_settings.json
```

## Сетевой transport

`core/http_transport.py` — единый low-level HTTP transport для updater и sharing. Он остаётся Qt/DCC-independent. Legacy Windows/Python 2 может использовать PowerShell/.NET fallback с TLS 1.2; callers получают единый `TransportError` contract.

## Compatibility policy

Item architecture намеренно не имеет compatibility layer для pre-v21 Item shape: нет flat Item view, schema `20 -> 21` migration, dual registry и legacy factory routing.

Compatibility для внешних platform/runtime требований остаётся допустимой, например `qt_compat.py` и legacy Windows/Python HTTP transport. Она не должна становиться второй Item architecture.

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
    items.py
    layouts.py
    item_definitions/
      __init__.py
      image.py

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
- Persisted/runtime Item использует только schema 21 envelope; flat compatibility view не добавляется.
- Unknown item kind нельзя silently convert в другой kind.
- `kind` — единственный type discriminator.
- `ui.label` нельзя использовать как identity.
- Event behavior сохраняется только в `bindings`.
- Новый Item type регистрируется через `ItemTypeDefinition`; core, palette, events, runtime и Inspector routing выводятся из metadata без central kind tables.
- Structural recursion и editor containment используют registry capabilities.
- Section traversal называется `include_sections`; folder-specific compatibility naming не поддерживается.
- Qt compatibility принадлежит `qt_compat.py`.
- UI/runtime composition ordering принадлежит `ui/bootstrap.py`.
- Source остаётся Python 2.7 compatible, пока поддержка Maya 2015 / Nuke 12 не будет намеренно прекращена.
