# Updater

Script Toolbox использует два GitHub-backed канала обновления:

- `Stable` читает последний обычный GitHub Release, опубликованный из `main`.
- `Development` читает перемещаемый prerelease `dev-latest`, публикуемый из `dev`.

Stable остаётся каналом по умолчанию.

## Поведение Runtime

1. Главное окно запускает проверку обновлений в background QThread.
2. Выбранный update channel загружается из `script_toolbox_settings.json`.
3. Если обновление доступно, top bar показывает `UPDATE <version>`.
4. Пользователь явно подтверждает установку.
5. Updater скачивает packaged ZIP выбранного канала.
6. Если HTTPS stack Python 2.7 в Maya 2015 на Windows не может обратиться к GitHub, updater прозрачно переключается на PowerShell/.NET TLS 1.2 без открытия console window.
7. Если присутствует SHA-256 asset, скачанный ZIP проверяется до extraction.
8. Update сначала staging и validation, затем заменяется live package.
9. Если activation завершается ошибкой, transaction восстанавливает предыдущий package.
10. Существующий Toolbox UI закрывается, все дочерние модули `script_toolbox.*` выгружаются, package root перезагружается на месте, и Toolbox снова открывается уже из новых файлов.
11. Перезапуск DCC требуется только как fallback, если hot reload не удался или будущий release добавит native binaries, которые нельзя безопасно выгрузить.

Конфигурация toolbox находится вне package и не заменяется. Preferences канала обновления хранятся отдельно от `maya_script_toolbox.json`.

## UI канала обновления

Tool button Check for Updates имеет стрелку меню.

Меню содержит:

- `Stable`
- `Development`

Смена канала сохраняет выбор и сразу проверяет вновь выбранный канал.

## Stable releases

`scripts/script_toolbox/constants.py` содержит текущую semantic version, например:

```python
PLUGIN_VERSION = "0.8.5"
```

Когда stable version попадает в `main`, сначала выполняется workflow `Python checks`. После успешного завершения `.github/workflows/release.yml` собирает и проверяет package, при необходимости создаёт tag `v<version>` и публикует GitHub Release.

Версии с prerelease suffix вроде `-dev` пропускаются stable release workflow.

## Development builds

Каждый push в `dev` запускает `.github/workflows/dev-build.yml`.

Workflow вызывает обычные Python checks как reusable workflow. Только после их успеха он:

1. формирует development version вроде `0.8.5-dev.42`;
2. stamps package значениями `BUILD_CHANNEL = "development"`, workflow build number и commit SHA;
3. собирает package и checksum;
4. перемещает tag `dev-latest` на протестированный commit;
5. создаёт или обновляет один GitHub prerelease `dev-latest`.

Prerelease всегда содержит три asset:

- `script-toolbox-dev.zip`
- `script-toolbox-dev.zip.sha256`
- `dev-manifest.json`

Старые Development releases не накапливаются. Единственный prerelease `dev-latest` обновляется на месте.

Stable updater использует endpoint последнего обычного GitHub Release, поэтому prerelease `dev-latest` не становится Stable update.

## Свежесть Development

Development builds используют GitHub Actions run number как монотонно возрастающий build number.

Если установленный package уже является Development build, updater предлагает Development update только когда build number у `dev-latest` больше установленного `BUILD_NUMBER`.

Переход со Stable на Development всегда предлагает текущий `dev-latest`. Переход с Development build обратно на Stable использует обычное semantic-version comparison; stable release с той же numeric version выше его development prerelease.

## Публичный репозиторий

Репозиторий публичный, поэтому проверки обновлений и скачивание release не требуют GitHub token.

Updater сохраняет поддержку `SCRIPT_TOOLBOX_GITHUB_TOKEN` для совместимости с private forks. Tokens читаются только из process environment и никогда не записываются в toolbox configuration или update settings.

## Ручная проверка обновлений

Top bar содержит кнопку Check for Updates. Ошибки проверки показываются в status bar Toolbox вместо молчаливого игнорирования.

## Поведение при ошибках

Ошибки download/install показываются пользователю, а updater пытается восстановить предыдущий package через существующий transaction mechanism.

Если installation успешна, но hot reload завершается ошибкой, новые файлы остаются установленными и Script Toolbox просит перезапустить host application.
