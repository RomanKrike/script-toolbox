# Обновления

У Script Toolbox два канала: **Stable** читает последний обычный GitHub Release из `main`, **Development** — перемещаемый prerelease `dev-latest` из `dev`. По умолчанию выбран Stable. Updater выбирает пакет плагина или Windows standalone в зависимости от запущенной установки.

## Управление обновлениями

- **Settings → Check for Updates** запускает ручную проверку.
- **Settings → Update Channel → Stable / Development** меняет канал и сразу проверяет обновления.
- **Settings → Open Settings → General → Update channel** позволяет изменить ту же настройку.

Проверка выполняется в background QThread. Доступное обновление отображается как `UPDATE <version>` в верхней панели; установка требует подтверждения. Ошибки показываются в status bar или диалоге.

## Проверенная установка

Updater скачивает официальный ZIP и соответствующий `.sha256` через `core.http_transport`. Контрольная сумма проверяется до recovery, распаковки, staging и активации. Если пакет или checksum отсутствует либо проверка не прошла, установка останавливается. Архивы GitHub **Source code** не используются как запасной вариант установки.

Активация зависит от пакета:

| Пакет | Активация |
| --- | --- |
| Плагин DCC | Общий пакет подготавливается, проверяется и активируется; модули Script Toolbox перезагружаются, окно открывается снова. При ошибке hot reload требуется перезапуск DCC. |
| Windows standalone | Portable-пакет подготавливается, приложение закрывается, внешний helper активирует обновление и перезапускает `ScriptToolbox.exe`. Если автоматический перезапуск нельзя запланировать, UI просит выполнить его вручную. |

При ошибке активации используются rollback/recovery. Portable-обновление отслеживает подтверждение перезапуска и не перезагружает работающий native Python/Qt runtime на месте. Пользовательская конфигурация и настройка канала сохраняются. См. [Standalone](STANDALONE.md).

`core.update_transaction.install_release()` — публичная точка установки; portable-процесс передаётся в `core.standalone_update`. `core.updater.install_release()` делегирует ей вызов. Metadata релиза и работа с архивами находятся в `core.updater`, сетевое выполнение — в `core.http_transport`.

## Файлы стабильного релиза

Для версии 1.1.0 публикуются:

| Пакет | Архив |
| --- | --- |
| Плагин DCC | `script-toolbox-1.1.0.zip` |
| Windows standalone | `script-toolbox-1.1.0-standalone-windows-x64.zip` |

У каждого ZIP есть файл `.zip.sha256`. `release-build.json` содержит версию, исходный коммит и хеши обоих архивов.

После успешных push-проверок `main` workflow `.github/workflows/release.yml` собирает оба пакета из проверенного коммита. Проверяются версии, контрольные суммы и совпадение общего исходного кода. Затем создаётся тег версии, файлы загружаются в draft и полный релиз публикуется. Проверки pull request не запускают автоматическую публикацию. Также поддерживается явный workflow dispatch на `main`. Опубликованные версии пропускаются без перезаписи; версии с prerelease-суффиксом вроде `-dev` не публикуются этим stable workflow.

## Публикация Development

Каждый push в `dev` запускает `.github/workflows/dev-build.yml`. После Python checks собираются оба пакета с одинаковой development-версией и metadata канала, номера запуска и коммита. Оба пакета проверяются до публикации.

Prerelease `dev-latest` содержит:

- неизменяемые версионированные ZIP плагина и standalone с отдельными checksum;
- aliases плагина `script-toolbox-dev.zip` и `script-toolbox-dev.zip.sha256`;
- aliases standalone `script-toolbox-standalone-dev.zip` и `script-toolbox-standalone-dev.zip.sha256`;
- `dev-manifest.json`, публикуемый последним: он связывает типы пакетов с версионированными файлами и их хешами.

Тег `dev-latest` перемещается после полной публикации. Stable читает последний обычный релиз, поэтому development prerelease не становится обновлением Stable.

## Сравнение версий

Development build number растёт с номером workflow run. Для установленной Development-сборки предлагается версия с большим build number. При переходе Stable → Development предлагается текущая dev-сборка. Обратный переход использует semantic version comparison: стабильная версия выше development prerelease с тем же числовым номером.

Оба канала используют одну пользовательскую конфигурацию хоста. Перед проверкой изменений схемы экспортируйте backup. Обычные configs используют schema 21, configs со связанными пресетами — schema 22 и требуют 1.1.0 или новее. Старые configs автоматически не мигрируют.

## Сеть и прокси

Updater и encrypted sharing используют общий transport и настройки **Settings → Open Settings → Network**: System, No proxy или Manual (HTTP, HTTPS, SOCKS5; опциональная авторизация).

В современном Windows сначала используется `urllib`, затем скрытый PowerShell/.NET fallback. В legacy Windows/Python 2 порядок обратный. На других платформах используется `urllib`. PowerShell использует TLS 1.2 и явные timeouts. Ошибки приводятся к `TransportError`/`UpdateError`.

В Windows пароль прокси защищён ключом DPAPI пользователя. Без безопасного credential backend пароль не сохраняется. Для публичного репозитория GitHub token не нужен. Private forks могут использовать `SCRIPT_TOOLBOX_GITHUB_TOKEN` из окружения; токен не сохраняется в настройках и не вставляется в командную строку PowerShell.
