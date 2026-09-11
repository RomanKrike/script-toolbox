# Архитектура

Script Toolbox — модульный multi-DCC toolbox для Maya, Nuke и Houdini с общей моделью и core-слоем.

## Целевая совместимость

### Maya
- Autodesk Maya 2015
- Python 2.7
- PySide 1 / Qt 4
- Python и MEL для event scripts

### Nuke
- Nuke 12
- Python 2.7
- PySide2 / Qt 5
- Python для event scripts

### Houdini
- Houdini 19.0
- стандартная сборка Python 3.7
- PySide2 / Qt 5
- Python и HScript для event scripts

Исторические схемы конфигурации Script Toolbox намеренно **не** являются целью совместимости, пока плагин активно развивается.

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

core/http_transport -> только Python stdlib
core/executor -> hosts
model -> pycompat (pure Python)
hosts/base -> только Python stdlib
hosts/maya_host -> maya.cmds / maya.mel
hosts/nuke_host -> nuke / nukescripts
hosts/houdini_host -> hou
```

Слой model должен импортироваться без Maya и Qt. Host-specific imports находятся за `hosts/`, `compat.py` и модулями интеграции конкретных DCC. `core/http_transport.py` не зависит от Qt/DCC и не должен импортировать UI.

## Пути пользовательской конфигурации

`core/user_paths.py` — единственный владелец логики определения runtime-путей config/settings. Stable и Development используют одну и ту же host-specific пользовательскую папку и одинаковые канонические файлы. Отдельного test/dev runtime config path и environment-variable override для config/settings нет.

Для Maya канонические файлы:

```text
<cmds.internalVar(userPrefDir=True)>/maya_script_toolbox.json
<cmds.internalVar(userPrefDir=True)>/script_toolbox_settings.json
```

Код, которому нужны временные пути для тестов или import/export, передаёт явный `path=` в соответствующий API config/preferences; выбор runtime path остаётся централизованным.

## Текущая схема конфигурации

Schema **20** — единственный поддерживаемый контракт конфигурации.

```text
JSON read
  -> validate schema version 20
  -> normalize current-schema values/defaults
  -> runtime document
```

Непустой документ без version, старая schema и более новая schema отклоняются. Config-слой не определяет, не мигрирует и не down-convert исторические payloads. Пустой mapping используется внутри только для создания нового документа актуальной схемы.

Breaking schema changes во время разработки могут повышать `CONFIG_VERSION`, но репозиторий хранит только текущий schema contract и current-schema tests, пока обратная совместимость не будет явно возвращена как product requirement.

## Контракты item model

Семантика контейнеров принадлежит model-слою. `folder`, `row` и `column` — канонические container kinds; document traversal, indexing, reference rewriting, cloning, topology и cache logic используют общий container predicate и канонический `walk_items()`.

Создание элементов принадлежит model factory registry. `button`, `toggle_button`, `icon`, `toggle_icon`, value controls, `row`, `column` и `folder` — native item kinds. Неизвестные kinds отклоняются вместо молчаливого преобразования в другой тип.

Идентичность имеет один явный контракт:

- `id` — канонический стабильный внутренний идентификатор и предпочтителен для долговечных ссылок;
- `name` — поддерживаемый символический идентификатор для скриптов и человекочитаемого API;
- `label` — только presentation text и никогда не участвует в lookup.

`bindings` — единственный persisted/runtime event mechanism. Callback dictionaries и прямые script fields не читаются и не переводятся. Обычный `button` — только action. Stateful-поведение принадлежит `toggle_button` и `toggle_icon` через native handler `state_toggle`.

Для alignment у Icon и Toggle Icon единственный schema key — `content_alignment`. `alignment` не является alias.

Создание numeric scalar/vector и runtime writes используют один normalizer, поэтому size, min/max clamping, component count и fallback behavior не могут расходиться.

## Архитектура Editor

`EditorDocumentController` владеет staged document, identity cache, clone/reference operations и topology. Он не зависит от Qt.

Активный Interface Editor объединяет controller ownership, command history, helpers дерева Row/Column, search presentation, sharing и сохранение view-state через `ui/editor_document_adapter.py`.

`ui/layout_editor_adapter.py` содержит только helper functions; он не публикует второй editor wrapper class или отдельный layout document controller. Небольшой marker на активном document adapter нужен только для предотвращения двойного wrapping во время development hot reload.

## Lifecycle UI composition

`ui/bootstrap.py` — composition root для UI/runtime. Он владеет упорядоченным построением финальных классов `InterfaceEditor` и `ScriptToolbox`, настройкой runtime renderer registry и установкой оставшихся compatibility hooks.

`ui/__init__.py` теперь максимально декларативен. Для обратной совместимости импорт `script_toolbox.ui` по-прежнему автоматически инициализирует полный UI, но package import содержит один явно видимый composition call:

```python
_RUNTIME = initialize_ui()
```

Полученный `UIComposition` хранит финальные public classes и активный runtime renderer registry. Поэтому существующие public imports `from script_toolbox.ui import ScriptToolbox` и `from script_toolbox.ui import InterfaceEditor` сохраняют прежний контракт.

`initialize_ui()` идемпотентен в пределах одного загруженного module graph: успешно созданная composition кэшируется и возвращается при повторных вызовах. Ошибка composition не кэшируется, поэтому последующий вызов может восстановиться. В hook-модулях остаются только markers, которые действительно нужны для предотвращения повторного wrapping, event filters или замены методов.

Для development hot reload bootstrap повторно использует активный renderer registry, если объект модуля runtime не изменился. Это сохраняет third-party renderer registrations и registry-owned install markers при reload только composition-модуля. Если перезагружен сам `ui.runtime`, bootstrap создаёт новый default registry для новых runtime classes. Built-in renderers регистрируются с явной заменой, поэтому повторная composition не накапливает дубликаты.

Оставшаяся подмена telemetry-aware share installer внутри `editor_document_adapter` — намеренно локализованный transitional compatibility monkeypatch. Теперь он находится только в composition root, а не размазан по package import logic. Удаление этой adapter-global зависимости отложено до отдельного безопасного изменения, чтобы не сломать direct builder imports.

## Runtime rendering

`RuntimeFolder.build_runtime_widget()` обращается непосредственно к runtime renderer registry. Lifecycle registry теперь принадлежит UI bootstrap. Base renderers инициализируются один раз для активного runtime module, а специализированные актуальные kinds явно регистрируются composition root.

Runtime event filters подключают поддерживаемые mouse/editing/selection events к отрендеренным widgets и dispatch через `bindings`. Renderer-specific modules не патчат event semantics главного окна.

Stateful execution и refresh принадлежат главному runtime API. Renderers Toggle Button и Toggle Icon только создают и регистрируют widgets.

## Сетевой transport

`core/http_transport.py` — единый низкоуровневый HTTP transport для updater и sharing. Callers передают URL, payload, headers и timeout и получают bytes/file output либо `TransportError`; им не нужно знать о `urllib`, subprocess, TLS setup или построении PowerShell command.

Transport policy:

- non-Windows: только Python `urllib`;
- modern Windows/Python: сначала `urllib`, затем PowerShell/.NET fallback при transport failure;
- legacy Windows/Python 2: сначала PowerShell/.NET, потому что HTTPS stack старого host Python может не поддерживать современное TLS/certificate/SNI поведение, затем `urllib` fallback при ошибке PowerShell;
- если на modern Windows реально понадобился успешный PowerShell fallback, текущий процесс предпочитает PowerShell для следующих shared transport calls.

PowerShell transport использует .NET `HttpWebRequest`, TLS 1.2, hidden-process startup flags и явные request/read-write timeouts. Authorization передаётся дочернему процессу через временную environment variable и не встраивается в command line. Request body и response download используют временные/binary files там, где это необходимо, поэтому updater и sharing больше не содержат собственных PowerShell HTTP implementations.

`core.updater` преобразует transport failures в `UpdateError`; `share.provider` — в `ShareProviderError`.

## Политика compatibility

Compatibility symbols классифицируются по фактическому использованию: внутренний dead code можно удалять только после repository-wide usage check; потенциально внешние imports сохраняются как маленькие forwarding/no-op shims до намеренного breaking change.

Текущие compatibility layers:

- private transport helpers updater, например `_download_with_powershell`, теперь делегируют в `core.http_transport`;
- private Windows/PowerShell helpers share provider также делегируют в `core.http_transport`;
- `ui/icon_ui_hooks.py` сохранён как документированный набор no-op shims для старых direct imports;
- часть base-методов `InterfaceEditor`, переопределяемых production adapter chain, пока сохраняется из-за возможных direct module imports;
- `install_runtime_folder_chrome` остаётся forwarding compatibility alias.

Эти compatibility layers не должны снова превращаться в независимые реализации. Новый production flow должен использовать канонические API напрямую.

## Текущая структура пакета

```text
scripts/script_toolbox/
  __init__.py
  bootstrap.py
  compat.py
  pycompat.py
  constants.py
  nuke_integration.py
  houdini_integration.py

  hosts/
    base.py
    maya_host.py
    nuke_host.py
    houdini_host.py

  core/
    config.py
    config_schema.py
    user_paths.py
    editor_commands.py
    editor_document.py
    event_bindings.py
    executor.py
    http_transport.py
    references.py
    runtime_registry.py
    values.py
    updater.py

  model/
    __init__.py
    bindings.py
    index.py
    items.py
    layouts.py

  style/
    ...

  ui/
    __init__.py
    bootstrap.py
    main_window.py
    debounced_main_window.py
    runtime.py
    runtime_renderers.py
    editor_document_adapter.py
    layout_editor_adapter.py
    ...

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
```

## Правила

- Никаких circular imports.
- Никакого DCC UI/API-кода в `model`.
- Host-specific API access находится в `hosts/` или host integration modules.
- Никакого JSON file I/O в `ui`.
- Runtime config/settings paths принадлежат только `core/user_paths.py`.
- Stable и Development используют одни канонические пользовательские config files.
- Пока проект находится в разработке, поддерживается только текущая config schema.
- Неизвестный item kind нельзя молча преобразовывать в другой kind.
- `label` нельзя использовать как identity элемента.
- Event behavior сохраняется только в `bindings`.
- Icon alignment сохраняется только как `content_alignment`.
- Новые item types регистрируются через model, renderer и property-editor registries.
- Structural recursion использует общий container predicate.
- Shared network compatibility принадлежит `core/http_transport.py`; updater/share не должны дублировать PowerShell transport logic.
- Порядок UI/runtime composition принадлежит `ui/bootstrap.py`; `ui/__init__.py` должен оставаться небольшим public export surface.
- Исходный код остаётся совместимым с Python 2.7 до намеренного прекращения поддержки Maya 2015.
