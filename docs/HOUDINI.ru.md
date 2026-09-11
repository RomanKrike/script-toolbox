# Интеграция с Houdini 19

Script Toolbox поддерживает Houdini 19.0 как один из целевых DCC-хостов.

## Целевая совместимость

Начальная цель для Houdini:

- Houdini 19.0
- стандартные сборки Python 3.7
- PySide2 / Qt 5
- Python и HScript для button scripts

Host adapter также сохраняет синтаксическую совместимость с Python 2.7, потому что Houdini 19.0 был последним семейством Houdini с отдельно публиковавшимися Python 2-сборками.

## Установка для разработки

Репозиторий не нужно копировать в preferences Houdini. Вместо этого укажите Houdini на папку `scripts` репозитория.

Простой package-файл можно создать здесь:

```text
$HOUDINI_USER_PREF_DIR/packages/script_toolbox.json
```

Пример:

```json
{
    "env": [
        {
            "SCRIPT_TOOLBOX_ROOT": "C:/path/to/script-toolbox"
        },
        {
            "var": "PYTHONPATH",
            "value": "$SCRIPT_TOOLBOX_ROOT/scripts",
            "method": "prepend"
        }
    ]
}
```

Замените `C:/path/to/script-toolbox` на путь к локальному checkout.

После перезапуска Houdini откройте Python Shell или shelf tool и выполните:

```python
import script_toolbox
script_toolbox.show()
```

Для reload во время разработки:

```python
import script_toolbox
script_toolbox.reload_toolbox()
```

## Поведение хоста

В Houdini Script Toolbox использует модуль `hou` для:

- определения версии Houdini;
- чтения выбранных nodes;
- восстановления выделения nodes из Field list items;
- проверки существования объектов;
- selection-change callbacks;
- выполнения HScript;
- получения `$HOUDINI_USER_PREF_DIR`.

Python button scripts получают и `host`, и `hou` в execution namespace.

Главное окно Script Toolbox становится дочерним для Qt main window Houdini. Интеграция предпочитает `hou.qt.mainWindow()` и сохраняет `hou.ui.mainQtWindow()` как compatibility fallback.

## Текущий scope

Это первый слой интеграции Houdini. Он покрывает общий Runtime и Editor Script Toolbox как обычное Qt-окно.

Нативный Houdini Python Panel descriptor и packaged release installer намеренно оставлены отдельной последующей задачей. Их стоит добавлять после проверки Houdini 19 Runtime в реальной сессии Houdini.
