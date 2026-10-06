# Managed Presets

Текущий формат и пользовательский workflow описаны в [Preset Library](PRESET_LIBRARY.ru.md).
Библиотека — корневой `library.json` и читаемые JSON в папках хостов и категорий.
Предыдущий индексированный формат не поддерживается.

## References

References хранят стабильные source/preset/parameter ID, локальное имя и локальные
значения. Разрешение работает из проверенного кеша без доступа к сетевому диску
на Qt-потоке. При потере цели параметр остаётся видимым broken reference.
ПКМ поддерживает Reveal in Presets, Resolve и Convert to Local Copy.

Составные пресеты вставляют локальный layout и reference controls. Mapping
`props.scope` связывает source ID/name с локальными ID/name и переписывает
скриптовые ссылки внутри набора. Схема обычных конфигов — 21, с references — 22.
Резолвер держит полные in-memory definitions; синхронизация не меняет активный
runtime. Редактор применяет staged document явно через Apply/Accept.

## Технические компоненты

- `core/preset_sources.py`: пользовательские подключения и пути кеша.
- `core/preset_sync.py`: сканирование папок, валидация и локальные snapshots.
- `core/preset_library.py`: публикация читаемых JSON с проверкой и откатом.
- `core/preset_references.py`: разрешение ID и локальные overrides.
- `ui/managed_presets.py`: Settings, диалог Save Preset и каталог.
- `ui/preset_hooks.py`: сохранение и вставка в редакторе.
- `examples/preset-source/library.json`: пример метаданных.
- `examples/preset-source/All/General/pipeline.json`: пример пресета.
