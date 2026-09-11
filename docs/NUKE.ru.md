# Интеграция с Nuke

Script Toolbox поддерживает Nuke через ту же core-модель, Interface Editor, Runtime widgets, updater и JSON-схему, что используются в Maya.

## Целевая совместимость

Первый целевой вариант Nuke:

- Nuke 12
- Python 2.7
- PySide2 / Qt 5
- Python для button scripts

MEL доступен только когда активный хост — Maya.

## Установка

Распакуйте релиз Script Toolbox в постоянную папку, например:

```text
C:\Tools\script-toolbox-0.3.0
```

Добавьте папку `scripts` релиза в Python path Nuke из `~/.nuke/menu.py`:

```python
import os
import sys

ROOT = r"C:\Tools\script-toolbox-0.3.0"
SCRIPTS = os.path.join(ROOT, "scripts")

if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import script_toolbox
script_toolbox.register_nuke_menu()
```

Готовый пример для редактирования включён в релизы:

```text
nuke/menu.py.example
```

## Использование

Обычное плавающее окно:

```python
import script_toolbox
script_toolbox.show()
```

Регистрация dockable-панели Nuke:

```python
import script_toolbox
script_toolbox.register_nuke_panel()
```

После `register_nuke_menu()` эти действия также доступны из application menu Nuke.

## Namespace скриптов

Python-кнопки в Nuke получают:

```python
nuke
nukescripts
host
toolbox
```

Пример:

```python
for node in nuke.selectedNodes():
    if "disable" in node.knobs():
        node["disable"].setValue(True)
```

В Maya эквивалентный namespace содержит:

```python
cmds
mel
host
toolbox
```

## Selection Fields

Field с `Source = Selection` следует за текущим выделением активного DCC.

В Nuke сохраняются node names или full node names. Двойной клик может повторно выделить сохранённые nodes.

## Файлы конфигурации

Maya сохраняет существующий путь и имя файла:

```text
<maya user prefs>/maya_script_toolbox.json
```

Nuke использует:

```text
~/.nuke/nuke_script_toolbox.json
```

Оба хоста используют одну JSON-схему, поэтому конфигурации можно экспортировать и импортировать между ними. Host-specific scripts при этом должны использовать API соответствующего DCC.

## Обновления

GitHub Releases общие для обоих хостов. На Windows старый HTTPS stack Python 2.7 при необходимости может использовать скрытый PowerShell/.NET TLS transport.

Текущий пакет полностью Python/PySide, поэтому успешное обновление по возможности выполняет hot reload. Перезапуск хоста остаётся fallback-вариантом при неудаче reload.
