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
  -> normalize + validate current Item envelopes и typed props
  -> runtime document
```

Version validation и Item validation — отдельные слои. Непустой document без `version`, старая schema и более новая schema отклоняются до Item normalization. Current-schema Items затем проходят через model schema. Malformed typed props не заменяются silent default. Migration `20 -> 21` намеренно отсутствует. Эти финальные исправления не меняют persisted envelope, поэтому `CONFIG_VERSION` остаётся 21.

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

Unknown `kind` отклоняется, а не преобразуется в другой тип. `kind` — единственный discriminator; параллельного `type`, `UnknownItem`, `RawItem` или placeholder storage нет.

## ItemTypeRegistry

`model/item_registry.py` — authoritative extension point. Новый тип описывается `ItemTypeDefinition`, а общие подсистемы читают definition вместо параллельных списков `kind`.

Definition хранит:

- `kind`, `title`, `category`, `description`, `order`, `creatable`;
- typed `fields` как data contract для `props`;
- public `events` и `internal_events`;
- semantic `capabilities`, например `container`, `layout`, `section`, `has_value`, `state_toggle`, `resizable`, `field_widget`, `native_button`, `divider`;
- optional `LayoutSpec` и `SectionSpec` для явной semantic metadata;
- defaults для `ui` и bindings;
- optional `normalize_props` hook для cross-field invariants;
- `renderer_path` и `inspector_path` для lazy Qt-side resolution;
- после UI resolution — реальные `renderer` и `inspector` callables/classes.

Capabilities остаются authoritative semantic flags. Convenience properties вроде `definition.is_layout`, `definition.is_section`, `definition.layout_spec` и `definition.section_spec` делают generic consumers явными, не создавая hierarchy Item-классов.

Core routing больше не использует `_FACTORIES`, `EVENT_CAPABILITIES`, `LAYOUT_KINDS`, `CONTAINER_KINDS`, `FOLDER_TYPES`, `STATE_TOGGLE_KINDS`, central property-editor mapping, renderer switch или authored palette list.

Standard built-ins регистрируются `model/item_builtins.py`. Их `ItemTypeDefinition`/Field objects lazily создаются один раз на загруженный module graph `item_builtins` и повторно используются при последующих вызовах `register_builtin_items()`. Это убирает постоянное пересоздание schema objects и не вводит второй registry. Reload модуля естественно сбрасывает этот cache; `ITEM_TYPES` остаётся единственным authoritative registry текущих definitions.

Отдельно расширяемые built-ins находятся в `model/item_definitions/`; `Image` определён в `model/item_definitions/image.py` и включён через явный built-in bootstrap. Для нового built-in допустима только type-specific реализация плюс, максимум, одна запись в explicit bootstrap/import list.

`ui/item_ui_bootstrap.py` generic и re-entrant: он проходит по текущему `ITEM_TYPES`, разрешает ещё не разрешённые UI paths и записывает renderer/Inspector обратно в definition. `ui/runtime_renderers.py`, `ui/properties/registry.py`, bindings, values, Interface Editor containment и palette используют ту же registry metadata.

## Field schema и validation pipeline

Model предоставляет декларативные `TextField`, `BoolField`, `IntField`, `FloatField`, `ChoiceField`, `ColorField`, `PathField` и `ListField`. Field classes остаются model-only и не знают про Qt controls.

Field отвечает за default, поддерживаемый coercion/parsing, normalization и validation. Production pipeline для `props`:

```text
raw props
  -> field parsing / supported coercion
  -> field normalization, включая numeric bounds
  -> per-field validation
  -> ItemTypeDefinition.normalize_props cross-field hook
  -> final field validation
  -> canonical props
```

`ItemTypeDefinition.validate_props()` использует те же правила допустимого coercion для diagnostic validation. Canonical construction, `normalize_document()`, config load, Inspector writes и runtime value writes используют `ItemTypeDefinition.normalize_props()`, поэтому validation является частью реального data path.

Граница coercion определена явно:

- `IntField`: `"12"` может стать `12`; `"hello"` является ошибкой и не превращается в default.
- `FloatField`: numeric text может быть преобразован; произвольный text invalid.
- `ChoiceField`: case-insensitive text может разрешиться в один из declared choices; отсутствующий choice invalid.
- `BoolField`: принимает booleans, `1`/`0` и explicit case-insensitive strings `true`/`false`, `yes`/`no`, `1`/`0`; произвольная непустая строка invalid. В частности, `BoolField.normalize("false")` возвращает `False`, а не Python-семантику `bool("false") == True`.
- numeric/color bounds применяют clamp только после успешного parsing; parsing failure не является случаем bounds и приводит к validation error.

`FieldValidationError` описывает parse/validation failure конкретного Field. `ItemValidationError` — Item-level error contract с `kind`, optional `id`/`name`, `field`, ошибочным `value` и `reason`. Runtime value normalization передаёт текущие `id` и `name` в definition, поэтому runtime errors сохраняют тот же identity context, что config/editor validation.

Complex cross-field invariants остаются на уровне definition через `normalize_props`; Inspector не становится вторым validator. `PropertyEditorBase.write_to_item()` делает deep copy текущих valid props, type-specific Inspector пишет только в candidate, затем candidate проходит `normalize_item_props_candidate()`. `self.item["props"]` заменяется только после успешной normalization/validation. При ошибке candidate отбрасывается, а исходные valid props остаются без изменений. Universal `name`/`ui` edits намеренно не включены в эту минимальную транзакцию, чтобы не делать большой Inspector redesign.

## Layout semantics

Layout behavior задаётся explicit metadata, а не выводится из имён полей. Layout definition объявляет capability `layout` и `LayoutSpec`:

```python
LayoutSpec(
    axis="horizontal",
    distribution_field="distribution",
    cross_alignment_field="cross_alignment",
    equal_size_field="equal_sizes",
)
```

Любое поле semantic spec может быть `None`, если конкретный layout не поддерживает эту возможность. `axis` описывает текущие linear layouts и оставляет место для будущих Grid/Flow/Wrap/Stack semantics без обучения generic кода конкретным `kind` names.

Текущие Row/Column сохраняют существующие persisted prop names, чтобы не делать лишний schema churn:

```text
Row:    axis=horizontal, distribution_field=horizontal_distribution,
        cross_alignment_field=vertical_alignment, equal_size_field=equal_widths
Column: axis=vertical, distribution_field=vertical_distribution,
        cross_alignment_field=horizontal_alignment
```

`ui/properties/layout_adapter.py` получает эти имена через `definition.layout_spec`. В нём нет persisted Row/Column field-name routing и нет `kind == "row"` / `kind == "column"` dispatch. Type-specific Row/Column renderer/Inspector modules при этом естественно могут знать собственную schema.

Synthetic horizontal `Flow Layout` может использовать, например, `flow_policy`, `cross_policy` и `same_extent`; generic editor semantics продолжают работать через `LayoutSpec` без новых core kind checks.

## Section semantics

Section определяется capability `section`; `SectionSpec` задаёт только имя schema field, которое несёт section mode:

```python
SectionSpec(mode_field="display_mode")
```

Допустимые mode values принадлежат Field schema и не дублируются в `SectionSpec`:

```python
fields={
    "display_mode": ChoiceField(
        ("cards", "stack"),
        default="cards"
    )
}
```

Capability `section` **не** подразумевает property с именем `folder_type`. Generic runtime получает mode через `definition.section_mode(props)`, который использует `section_spec.mode_field` и делегирует normalization/validation declared Field. `SectionSpec` больше не хранит второй `modes` tuple. Folder сохраняет persisted `folder_type` через `SectionSpec(mode_field="folder_type")`, а `ChoiceField` остаётся единственным источником допустимых `collapsible` / `simple` / `tabs` / `radio`.

Future Card Section с `props.display_mode`, Accordion Section, Tool Group или Asset Group могут участвовать в generic section routing без изменения `ui/runtime.py` и без concrete-kind branch. Type-specific rendering behavior остаётся в renderer конкретного Item type.

## Добавление и регистрация Item type

Routing core менять не нужно.

Для built-in `video`:

1. добавить `model/item_definitions/video.py` с `ItemTypeDefinition`;
2. добавить renderer и специализированный Inspector;
3. включить `video_definition()` в explicit built-in bootstrap tuple;
4. добавить tests.

Пример обычного Item:

```python
from script_toolbox.model.fields import PathField
from script_toolbox.model.item_registry import ItemTypeDefinition

resource = ItemTypeDefinition(
    kind="file",
    title="File",
    fields={"source": PathField(default="")},
    renderer_path=".file_item:render_file",
    inspector_path=".file_item:FilePropertyEditor",
)
```

Пример layout type:

```python
from script_toolbox.model.item_registry import ItemTypeDefinition, LayoutSpec

flow = ItemTypeDefinition(
    kind="flow",
    title="Flow Layout",
    fields={...},
    capabilities=("container", "layout"),
    layout=LayoutSpec(
        axis="horizontal",
        distribution_field="flow_policy",
        cross_alignment_field="cross_policy",
        equal_size_field="same_extent",
    ),
    renderer_path=".flow_layout:render_flow",
    inspector_path=".flow_layout:FlowPropertyEditor",
)
```

Пример section type:

```python
from script_toolbox.model.fields import ChoiceField
from script_toolbox.model.item_registry import ItemTypeDefinition, SectionSpec

card = ItemTypeDefinition(
    kind="card_section",
    title="Card Section",
    fields={
        "display_mode": ChoiceField(
            ("cards", "stack"),
            default="cards"
        )
    },
    capabilities=("container", "section"),
    section=SectionSpec(mode_field="display_mode"),
    renderer_path=".card_section:render_card_section",
    inspector_path=".card_section:CardSectionPropertyEditor",
)
```

Для этих типов правки не требуются в `bindings.py`, `layouts.py`, runtime dispatch, `properties/registry.py`, `interface_editor.py`, `item_palette.py` или document normalization. Future/external code может вызвать `register_item_type()` напрямую и не менять built-in bootstrap.

Built-in `Image` — production proof обычного Item pattern. Test-only Video, Flow Layout и Card Section доказывают late runtime registration, custom layout semantics и section semantics с mode field, отличным от `folder_type`.

## Lifecycle внешней регистрации

External definitions, которые могут встречаться в persisted config, **должны быть зарегистрированы до config normalization/load**. Канонический future plugin startup order:

```text
initialize model
  -> register built-in Item types
  -> register external/plugin Item types
  -> load + normalize config
  -> initialize UI
```

Late registration после UI composition поддерживается для runtime-added types: re-entrant UI path resolution и runtime registry synchronization обнаружат новую definition. Но если config loading уже встретил unknown persisted `kind`, loader не обязан сохранять raw Item до возможной поздней регистрации plugin. Unknown persisted kinds остаются invalid по clean-break policy; placeholder compatibility layer не добавляется.

## Containers, bindings и values

Container semantics принадлежат definitions. Traversal, indexing, cloning, topology и reference rewriting используют capabilities и канонический `walk_items()`, а не tuple со списком container kinds.

Top-level sections выражаются capability `section`. `walk_items(document)` по умолчанию не возвращает section Items; `walk_items(document, include_sections=True)` включает их явно. Старого `include_folders` compatibility API нет.

Layout containers используют capability `layout`; generic editor rules не требуют проверки конкретного имени kind для containment semantics.

`bindings` — единственный persisted/runtime event mechanism. Callback dictionaries и прямые script fields не являются вторым event API. Обычный `button` action-only. Stateful semantics определяются capability `state_toggle`, а button chrome — `native_button`.

Toggle Button и Toggle Icon участвуют в generic value API только при `state_source == "internal"`. Script-driven toggle не получает искусственный `props.value` через `store_value()`.

Numeric scalar/vector construction и runtime writes используют одни и те же definition normalizers, поэтому size, min/max clamping и component count не расходятся. Invalid numeric content отклоняется вместо silent замены на unrelated fallback. Field сохраняет runtime semantics: scalar -> text, list/tuple -> list of text, single-value field берёт первый элемент списка.

Selection-backed Field refresh намеренно остаётся transient: он не вызывает `set_value()`, automatic save или rebuild. Сначала новый selection value проходит через `core.values.normalize_value()` и ту же Item schema, затем canonical value записывается в `props.value`, обновляется widget и `value_changed` dispatch-ится только если canonical value действительно изменился.

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

## Runtime rendering и synchronization

`RuntimeFolder.build_runtime_widget()` dispatch-ит через runtime renderer registry. Default registry строится из `definition.renderer` после generic UI binding resolution.

Initial registry composition, late Item discovery и manual `register_runtime_renderer()` сходятся в один semantic generic decoration function: `_decorate_runtime_renderer_registry(registry)`. Этот pipeline применяет event-binding wrappers и runtime-value wrappers. Их marker-based guards делают повторную synchronization идемпотентной: повторный запуск pipeline не создаёт wrapper-on-wrapper stacking.

Startup-only UI polish, installer которого имеет более широкие runtime-module responsibilities, например scroll-frame composition или существующие visual polish hooks, остаётся в bootstrap и не replay-ится автоматически при каждой late registration. Shared pipeline содержит только generic renderer decorators, которые безопасно повторять.

Runtime renderer получает raw universal Item envelope и явно читает `ui` / `props`. Runtime event filters подключают только events, объявленные definition, и dispatch-ят их через `bindings`. Runtime value synchronization capability-driven: обычные `has_value` Item регистрируют `RuntimeValueBinding`; специальный Field refresh определяется capability `field_widget`, а не concrete kind branch.

Explicit runtime renderer unregister сохраняется: synchronization не resurrect-ит disabled renderer только потому, что definition всё ещё содержит declarative path. Последующая explicit registration снова включает renderer и применяет тот же generic decoration pipeline.

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
- Поддерживается только current config schema 21.
- Persisted/runtime Item использует только schema 21 envelope; flat compatibility view не добавляется.
- Unknown item kind нельзя silently convert в другой kind и нельзя сохранять через placeholder Item.
- `kind` — единственный type discriminator.
- `ui.label` нельзя использовать как identity.
- Event behavior сохраняется только в `bindings`.
- Новый Item type регистрируется через `ItemTypeDefinition`; core, palette, events, runtime и Inspector routing выводятся из metadata без central kind tables.
- `LayoutSpec` содержит layout semantics; generic code не выводит их из concrete field names.
- `SectionSpec` указывает только semantic mode field; допустимые mode values принадлежат Field schema и не дублируются.
- Inspector type-specific props пишутся в candidate и коммитятся только после schema validation.
- Generic runtime value writes проходят Item schema normalization до mutation `props.value`.
- External Item types, которые могут присутствовать в config, регистрируются до config load/normalization.
- Structural recursion и editor containment используют registry capabilities.
- Section traversal называется `include_sections`; folder-specific compatibility naming не поддерживается.
- Runtime initial/late/manual renderer registration использует один idempotent generic decoration pipeline.
- Qt compatibility принадлежит `qt_compat.py`.
- UI/runtime composition ordering принадлежит `ui/bootstrap.py`.
- Source остаётся Python 2.7 compatible, пока поддержка Maya 2015 / Nuke 12 не будет намеренно прекращена.
