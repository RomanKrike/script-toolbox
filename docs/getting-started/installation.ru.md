# Установка

Script Toolbox распространяется как версионированный ZIP-архив через GitHub Releases. Архив содержит общий пакет `scripts/script_toolbox` и файлы интеграции для конкретных DCC-хостов.

## Поддерживаемые хосты

Один пакет поддерживает следующие поколения DCC:

- **Maya 2015+** — PySide / Qt 4 на Maya 2015–2016, PySide2 / Qt 5 на Maya 2017–2024 и PySide6 / Qt 6 на Maya 2025+;
- **Nuke 12+** — PySide2 / Qt 5 на Nuke 12–15 и PySide6 / Qt 6 на Nuke 16+;
- **Houdini 19+** — PySide2 / Qt 5 на Houdini 19–20.x; опционально PySide6 / Qt 6 в Qt 6-сборках Houdini 20.5; основные сборки Houdini 21 используют PySide6 / Qt 6, а отдельные Qt 5.15.2-сборки — PySide2; Houdini 22+ использует PySide6 / Qt 6.

Script Toolbox определяет Qt/PySide binding во время запуска и предпочитает binding, уже загруженный или выбранный самим DCC, поэтому отдельные пакеты плагина для Qt 4, Qt 5 и Qt 6 не нужны.

## Скачивание стабильного релиза

1. Откройте страницу **Releases** репозитория.
2. Скачайте `script-toolbox-<version>.zip` из последнего стабильного релиза.
3. Распакуйте архив в постоянную папку. Не запускайте плагин прямо из ZIP-файла.

Стабильные релизы собираются из `main`. Development-сборки создаются отдельно из `dev` и предназначены для тестирования будущих изменений.

## Maya

В релиз входит `MayaScriptToolbox.mod` для установки через модульную систему Maya.

Сделайте папку, содержащую `MayaScriptToolbox.mod`, доступной Maya через обычный module path. После подключения модуля откройте Script Toolbox из Python:

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

Script Toolbox поддерживает два канала обновления:

- **Stable** — опубликованные стабильные релизы из `main`;
- **Development** — тестовые сборки из `dev`.

Для обычной работы используйте Stable. Development выбирайте только когда намеренно тестируете следующий релиз.


## Сетевой прокси

Если Script Toolbox должен обращаться к GitHub или сервису sharing через прокси, откройте **Settings → Network**. Доступны режимы **System**, **No proxy** и **Manual**. Ручная настройка поддерживает HTTP, HTTPS и SOCKS5, опциональную авторизацию и встроенную проверку соединения.

В Windows сохранённый пароль прокси защищается ключом DPAPI текущего пользователя. На платформах без встроенного безопасного backend пароль не записывается открытым текстом и после перезапуска его потребуется ввести снова.

## Пользовательская конфигурация

Конфигурация toolbox и настройки хранятся вне установленного пакета, в пользовательской конфигурационной области соответствующего DCC. Stable и Development используют одно и то же расположение пользовательских файлов, поэтому переключение канала обновления не создаёт отдельную конфигурацию toolbox.
