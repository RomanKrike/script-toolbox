# Установка

Script Toolbox распространяется как версионированный ZIP-архив через GitHub Releases. Архив содержит общий пакет `scripts/script_toolbox` и файлы интеграции для конкретных DCC-хостов.

## Скачивание стабильного релиза

1. Откройте страницу **Releases** репозитория.
2. Скачайте `script-toolbox-<version>.zip` из последнего стабильного релиза.
3. Распакуйте архив в постоянную папку. Не запускайте плагин прямо из ZIP-файла.

Стабильные релизы собираются из `main`. Development-сборки создаются отдельно из `dev` и предназначены для тестирования будущих изменений.

## Maya

В релиз входит `MayaScriptToolbox.mod` для установки через модульную систему Maya.

Сделайте папку, содержащую `MayaScriptToolbox.mod`, доступной Maya через ваш обычный module path. После подключения модуля откройте Script Toolbox из Python:

```python
import script_toolbox
script_toolbox.show()
```

Для разработки или после изменения кода плагина на месте:

```python
import script_toolbox
script_toolbox.reload_toolbox()
```

## Nuke

В релиз входят папка `nuke` и файл `nuke/menu.py.example`. Добавьте общую папку `scripts` в Python path Nuke, затем используйте:

```python
import script_toolbox
script_toolbox.show()
```

Чтобы зарегистрировать меню приложения:

```python
import script_toolbox
script_toolbox.register_nuke_menu()
```

Чтобы зарегистрировать dockable-панель:

```python
import script_toolbox
script_toolbox.register_nuke_panel()
```

Подробности см. в [заметках по интеграции Nuke](../NUKE.md).

## Houdini

Добавьте папку `scripts` из релиза в `PYTHONPATH` Houdini, затем выполните:

```python
import script_toolbox
script_toolbox.show()
```

Для разработки:

```python
import script_toolbox
script_toolbox.reload_toolbox()
```

Подробности см. в [заметках по интеграции Houdini](../HOUDINI.md) и в примере package-файла `houdini/script_toolbox.json.example`.

## Каналы обновления

Script Toolbox поддерживает три канала обновления:

- **Stable** — опубликованные стабильные релизы из `main`;
- **Latest** — самая новая подходящая опубликованная версия;
- **Development** — тестовые сборки из `dev`.

Для обычной production-работы используйте Stable. Development выбирайте только когда намеренно тестируете следующий релиз.

## Пользовательская конфигурация

Конфигурация toolbox и настройки хранятся вне установленного пакета, в пользовательской конфигурационной области соответствующего DCC. Stable и Development используют одно и то же расположение пользовательских файлов, поэтому переключение канала обновления не создаёт отдельную конфигурацию toolbox.
