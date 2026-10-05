# Внешние Preset Sources и references

Старые документы schema 21 и встроенные presets сохраняют прежний формат.
Подключённые источники хранятся отдельно в preferences, пакеты — в
`<user_config_dir>/presets/managed/<source_id>`. Пользовательские configs
и presets не являются целью sync. Клиент никогда не пишет на сервер.

## Работа пользователя

Для первой локальной проверки в тестовом ZIP есть готовая папка
`examples/preset-source`. Подключить её через Add Source: появится Demo Studio
с меню Demo Shot (`sh001`, `sh002`, `sh003`). Сетевая папка для этого не нужна.
После Apply выбрать `sh002`, перезапустить Toolbox и проверить, что выбор
сохранился. Затем переименовать/переместить папку source: existing reference
должен продолжить работать из локального cache.

ZIP содержит общий Python package для DCC и Python standalone; это не новая
сборка Windows EXE. Установку в Maya/Nuke/Houdini выполнять через обычный
механизм подключения `scripts`. Python standalone запускается с этой папкой
в PYTHONPATH командой `python -m script_toolbox.standalone` (нужен PySide).

1. Settings → Preset Sources → Add Source: выбрать папку с `toolbox-source.json`.
   ID автоматически читается из manifest. Можно задать своё display name.
2. После sync открыть редактор → существующий Presets → категория источника.
   Новая вкладка в Create Parameters не создаётся.
3. ПКМ по параметру → Create Reference. Двойной щелчок также создаёт reference.
4. Reference появляется в Existing Parameters с иконкой связи. Apply/Accept
   сохраняет ссылку и создаёт обычный runtime control.
5. ПКМ по reference: Reveal in Presets, Resolve, Convert to Local Copy,
   Remove Reference. Convert поддерживает Undo/Redo. Remove не удаляет target.

Определение защищено от локального редактирования; рабочее значение control
можно менять как обычно. Копирование ссылки сохраняет target, но получает
новые локальные ID/name. Контейнеры и layouts не доступны как reference:
в категории источника показываются параметры внутри preset subtree.

Settings сохраняет изменения sources сразу, аналогично самостоятельным
операциям интеграции. Cancel общего Settings не отменяет уже выполненный sync.
Disabled source скрыт из каталога и не проверяется автоматически, но уже
созданные references продолжают работать из cache. Удаление source из настроек
делает его references broken при следующем применении/открытии; cache остаётся.

## Жизненный цикл

Registry хранит connections. SyncService проверяет manifest, копирует пакет в
staging, проверяет checksums и Items, активирует локальную generation.
PresetResolver загружает проверенный локальный snapshot и разрешает ссылки
до существующего механизма создания runtime Items.

Открытый Toolbox закрепляет revision каждого source. Автоматический sync
обновляет только cache. Новые определения применяются при следующем открытии,
Reload Config или явном Apply/Accept редактора. Редактор получает собственный
snapshot при открытии; нажатие Resolve не обращается к сети.

`manual`, `on_start`, `periodic` определяют автоматическую проверку/загрузку.
Периодический interval задаётся в минутах. `on_start` ограничен одной проверкой
за минуту между повторными открытиями. Работа с сетью выполняется в daemon
worker, без Qt/DCC API; UI получает результаты через timer. Закрытие диалога
не уничтожает работающий QThread: фоновые операции не владеют QObject.

## Формат source

```json
{
  "schema": 1,
  "id": "0media",
  "name": "0+ Media",
  "revision": 42,
  "presets": [
    {
      "id": "pipeline",
      "file": "revision-42/pipeline.json",
      "sha256": "<64 lowercase hexadecimal characters>"
    }
  ]
}
```

Source/preset IDs — lowercase ASCII letters, digits, `_`, `-`, до 128 символов.
Source ID не меняется при переименовании display name или смене пути.
Manifest по новому пути должен иметь тот же ID. Пути относительные, без `..`,
absolute paths, Windows drive/UNC paths и ссылок за root через symlinks.
Одинаковые portable file paths и IDs запрещены.

Connection в `preset_sources` пользовательских preferences:

```json
{
  "id": "0media",
  "name": "0+ Media",
  "remote_path": "\\\\server\\tools\\script-toolbox\\presets",
  "enabled": true,
  "update_policy": "periodic",
  "interval_minutes": 60
}
```

Preset JSON использует существующий формат `id`, `dcc`, `label`, `root`.
`root` — canonical Item; все опубликованные Items обязаны иметь стабильные ID.
Например один параметр:

```json
{
  "id": "pipeline",
  "dcc": "all",
  "label": "Pipeline",
  "root": {
    "kind": "menu",
    "id": "shots",
    "name": "shots",
    "ui": {"label": "Shot"},
    "props": {"items": ["sh001", "sh002"], "value": "sh001"},
    "bindings": []
  }
}
```

В `root` также можно хранить существующее preset subtree с параметрами.
Пакеты не могут содержать вложенные references. DCC filtering использует
`all`, `maya`, `nuke`, `houdini`, `blender` как у встроенных presets.

## Публикация администратором

Подготовить папку canonical preset JSON и выполнить:

```text
python tools/publish_preset_source.py --input ./studio-presets --output "//server/tools/script-toolbox/presets" --id 0media --name "0+ Media"
```

Утилита автоматически повышает revision, вычисляет SHA-256, проверяет Items,
публикует новую отдельную папку и атомарно заменяет manifest последним.
Это отдельный инструмент администратора; клиент его не вызывает.
Не редактировать файлы уже опубликованной revision на месте.
Старые серверные revisions можно удалять позже, после завершения sync клиентов.
При ручной публикации соблюдать тот же порядок и обновлять revision/checksums.

## Формат reference

```json
{
  "kind": "reference",
  "id": "<local instance ID>",
  "name": "shots",
  "ui": {"label": "Shot"},
  "props": {
    "source": "0media",
    "preset": "pipeline",
    "parameter": "shots",
    "target_kind": "menu",
    "state": {"value": "sh002"}
  },
  "bindings": []
}
```

На диске нет сетевого пути и resolved definition. `ui` нормализуется обычными
presentation defaults; label используется как подпись при broken target.
В runtime resolver сохраняет локальные ID/name, подставляет source definition
и нормализует локальное значение по актуальным правилам control.
Самоссылки скрипта на source ID/name переписываются существующим механизмом
rewrite references. Зависимости на другие параметры не импортируются автоматически.

Runtime provenance `_preset_reference` остаётся только в памяти.
Save/autosave/export проецируют runtime обратно в authored references;
редактор работает с authored document. Изменения runtime definitions не
становятся local overrides и не записываются в source.

Разные sources/presets могут иметь одинаковые parameter IDs.
Изменение label при прежнем technical ID обновляет подпись runtime.
Изменение типа target оставляет reference broken, сохранив его локальное
значение: автоматическая конвертация несовместимых типов не производится.

## Надёжность и состояния

Sync использует локальную staging-папку. Проверяются schema, source ID,
stable IDs, JSON, canonical Item definitions, SHA-256 и неизменность manifest
за время копирования. Затем staging переименовывается в immutable generation
и атомарно заменяется `active.json`, содержащий `current` и `previous`.
File locks исключают одновременную активацию/чтение/очистку поколений.
Локально сохраняются два поколения; runtime snapshots уже находятся в памяти.

Невалидная новая версия не активируется. Повреждённый current cache позволяет
прочитать previous. Сеть offline не мешает resolve при наличии валидного cache.

Состояния: `not_installed`, `up_to_date`, `update_available`, `syncing`,
`offline`, `invalid_source`, `sync_failed`. Дополнительно сохраняются local /
remote revision, last_check, last_sync и сообщение ошибки. Broken reference
не удаляется и отображается в редакторе и runtime, не мешая другим параметрам.

## Совместимость и ограничения

Без sources поведение прежних configs сохраняется; миграция не требуется.
Обычные configs продолжают записываться как schema 21. Только документы,
содержащие новый Item kind `reference`, записываются как schema 22. Новый build
читает оба варианта; внутри используется та же модель Items. Это защищает
от downgrade: старый build отвергает schema 22 до механизма восстановления
«повреждённого» config из backup и не подменяет документ без references.
После Convert/Remove всех references документ снова сохраняется как schema 21.
Export/share сохраняет links: получатель должен
подключить тот же source либо отправитель должен выполнить Convert to Local Copy.
Cache и network credentials не включаются в export/share.

Источники могут содержать scripts, которые исполняются через обычный runtime
при использовании parameters. Подключать следует доверенные студийные папки.
Sync validation проверяет структуру, но не исполняет scripts.

Вне scope: remote folders/layouts, live updates активного окна, local overrides,
dependency imports, marketplace, HTTP/Git/Drive sources и визуальный publisher.

## Проверка реализации

База: dev `b72682e`. Рабочая ветка: `feature/managed-presets`.

- Общий набор без Qt: 746 passed, 21 skipped (Qt / Windows проверки).
- Отдельный набор с реальным Qt: 42 passed, включая Create Reference,
  Apply, сохранение локального значения, Undo/Redo Convert и закрытие Settings
  во время background job.
- Фактический Python 2.7.18: compileall общего package и publisher, managed
  sync/reference/offline smoke, config save/load, UI import, Nuke/Houdini
  host import/callback smoke — успешно.
- Flake8 correctness checks и git diff --check — успешно.
- Внешний вид Settings и редактора просмотрен через offscreen Qt render.

Тесты используют временные каталоги. Production shares и реальные Share uploads
не используются. Нативные Maya/Nuke/Houdini и Windows EXE требуют ручной проверки
в соответствующих приложениях; тесты импорта не заменяют запуск настоящего DCC.

Изменённые и добавленные файлы:

| Область | Файлы |
|---|---|
| Core | `core/preset_sources.py`, `core/preset_sync.py`, `core/preset_references.py`, `core/config.py` |
| Model | `model/item_builtins.py`, `model/items.py` |
| UI | `ui/managed_presets.py`, `ui/preset_hooks.py`, `ui/interface_editor.py`, `ui/editor_document_adapter.py`, `ui/main_window.py`, `ui/settings_dialog.py` |
| Icons | `style/builtin_icons.py`, `resources/icons/solar/reference.svg`, `resources/icons/solar/NOTICE.txt` |
| Tests | `tests/test_managed_presets.py`, `tests/test_qt_managed_presets.py`, `tests/python2_managed_presets_smoke.py` |
| Tooling / docs | `tools/publish_preset_source.py`, `tools/build_release.py`, `.github/workflows/python-checks.yml`, `docs/MANAGED_PRESETS.ru.md` |
| Demo | `examples/preset-source/pipeline.json`, `examples/preset-source/toolbox-source.json` |

Пути Core/Model/UI/Icons приведены относительно `scripts/script_toolbox/`.
