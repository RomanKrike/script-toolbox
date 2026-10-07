# Standalone

Script Toolbox может работать как отдельное приложение Windows x64 без Maya, Nuke и Houdini. Оно использует тот же пакет `scripts/script_toolbox`, UI, модель элементов, bindings, пресеты и ресурсы, что и DCC-плагин.

## Установка и запуск

Доступно в stable **1.1.0 и новее**. Скачайте `script-toolbox-<version>-standalone-windows-x64.zip` и соответствующий `.sha256` со страницы [GitHub Releases](https://github.com/RomanKrike/script-toolbox/releases/latest). Распакуйте весь архив и запустите `S/ScriptToolbox.exe`. EXE, runtime, scripts и bootstrap должны оставаться вместе. Установщик, права администратора и системный Python не нужны.

Соберите интерфейс через **Editor → Open Editor** или импортируйте JSON. Подключайте проектные библиотеки через **Settings → Open Settings → Preset Library**; см. [Библиотеки пресетов](guide/preset-libraries.md). Для установки меню/shelf DCC откройте **Settings → Open Settings → DCC Integrations**.

## Обновления

Используйте **Settings → Check for Updates**. Updater выбирает standalone-пакет выбранного канала Stable/Development, проверяет checksum и подготавливает portable-обновление. Приложение закрывается; внешний helper активирует пакет и перезапускает `ScriptToolbox.exe`. Если автоматический перезапуск нельзя запланировать, UI просит перезапустить приложение вручную. При ошибке активации выполняется откат. Подробнее: [Updater](UPDATER.md).

## Структура пакета

```text
S/
├── ScriptToolbox.exe
├── runtime/
├── scripts/
│   └── script_toolbox/
├── standalone/
│   └── bootstrap.py
├── MayaScriptToolbox.mod
├── nuke/
└── houdini/
```

DCC используют свой Python/Qt и общий каталог `scripts`. Native launcher загружает Python DLL из `runtime` в свой процесс и вызывает `standalone/bootstrap.py`. Окно принадлежит `ScriptToolbox.exe`, а не дочернему `python.exe` или `pythonw.exe`. Пути определяются относительно EXE; Windows AppUserModelID — `ScriptToolbox.App`.

## Запуск из исходников

При доступном пакете и подходящем Qt binding:

```text
python -m script_toolbox.standalone
```

Создаётся `QApplication`, если её ещё нет, вызывается общий `show()` и запускается Qt event loop. `StandaloneHost` предоставляет Python без DCC selection, родительского окна DCC и эмуляции DCC API.

## Сборка portable

`.github/workflows/standalone-build.yml` подготавливает официальный embeddable Python 3.11, устанавливает PySide6 внутрь runtime, компилирует native launcher с Windows metadata и иконкой, затем собирает ZIP через `tools/build_standalone_portable.py`. Проверяются UI lifecycle, запуск EXE и native update с автоматическим перезапуском. ZIP и checksum сохраняются как workflow artifacts.

Stable workflow вызывает эту сборку и публикует standalone вместе с пакетом плагина после проверки обоих архивов.

## Пользовательские данные

Пути определяются общим `core/user_paths.py`; имя конфигурации standalone по умолчанию — `script_toolbox.json`. Обычные configs используют schema 21, configs со связанными пресетами — schema 22 и требуют 1.1.0 или новее. Loader общий для standalone и DCC; автоматической миграции старых схем нет.

## Ограничения

DCC-скрипты требуют соответствующего хоста: например, `import maya.cmds` не работает в standalone. Приложение не эмулирует Maya/Nuke/Houdini API. Python bindings могут запускать другие приложения, например через `subprocess.Popen(...)`.

## Панель задач Windows

После извлечения нового пакета:

1. Удалите старое закрепление Script Toolbox/Python.
2. Запустите новый `ScriptToolbox.exe` и проверьте название Script Toolbox в меню панели задач.
3. Закрепите приложение, закройте его и запустите с закреплённой иконки.
4. Проверьте название, иконку и отсутствие отдельной группы Python.

Если Windows показывает старую иконку, удалите старый ярлык и закрепите новый EXE. Explorer и панель задач кешируют иконки; иногда требуется обновление кеша Shell.
