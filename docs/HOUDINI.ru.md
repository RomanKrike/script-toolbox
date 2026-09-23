# Интеграция с Houdini

Script Toolbox поддерживает Houdini 19 и новее через общую host/runtime-архитектуру.

## Целевая совместимость

Поддерживаемые поколения Houdini:

- Houdini 19–20.x в стандартных Qt 5-сборках — PySide2 / Qt 5
- опциональные Qt 6-сборки Houdini 20.5 — PySide6 / Qt 6, когда хост выбирает этот binding
- основные сборки Houdini 21 — PySide6 / Qt 6; отдельные Qt 5.15.2-сборки также поддерживаются через PySide2
- Houdini 22+ — PySide6 / Qt 6; Qt 5-сборки были прекращены начиная с Houdini 22
- Python и HScript для button scripts

Host adapter сохраняет синтаксическую совместимость с Python 2.7, потому что Houdini 19.0 был последним семейством Houdini с отдельно публиковавшимися Python 2-сборками.

Script Toolbox определяет binding по версии Houdini, `HOUDINI_QT_PREFERRED_BINDING` и binding, уже загруженному самим хостом. Уже загруженный или явно выбранный хостом binding имеет приоритет, чтобы Script Toolbox намеренно не смешивал разные Qt major в одном процессе Houdini. Это также позволяет отдельным Qt 5-сборкам Houdini 21 выбирать PySide2, тогда как основная сборка Houdini 21 использует PySide6.

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

## Qt compatibility

Общий UI сохраняет исходный Qt 4-style namespace widgets через `QtGui`. На PySide2 и PySide6 Script Toolbox зеркалирует `QtWidgets` в этот namespace, поэтому Runtime и Interface Editor не требуют отдельных реализаций для разных поколений Houdini.

Compatibility layer также предоставляет нужную поверхность Qt 6 для существующего Editor: используемый subset `QRegExp`, legacy aliases `exec_()`, font-metric width и современный tab-stop API.

## Текущий scope

Общий Runtime и Interface Editor Script Toolbox работают как обычное Qt-окно во всех поддерживаемых поколениях Houdini.

Нативный Houdini Python Panel descriptor и packaged release installer остаются отдельными последующими задачами. Их следует валидировать независимо от cross-version runtime compatibility layer.
