# Архитектура телеметрии

Телеметрия Script Toolbox опциональна, включается только по явному согласию пользователя и не привязана к конкретному provider.

Core плагина не должен напрямую зависеть от PostHog, Aptabase или любого будущего analytics service. Feature-код отправляет только семантические события через facade `script_toolbox.telemetry`.

## Контракт приватности

Телеметрия должна оставаться выключенной, пока пользователь явно не согласится на её отправку.

Сохраняемая настройка имеет три состояния:

- `None` — пользователь ещё не ответил;
- `True` — пользователь явно согласился;
- `False` — пользователь явно отказался.

Наличие настроенного provider не означает consent. Application bootstrap включает telemetry только когда `get_telemetry_consent()` строго равен `True`.

После явного opt-in Script Toolbox создаёт случайный псевдонимный installation identifier. Он не вычисляется из hardware, username, hostname, Autodesk/account data, сцен, проектов или filesystem data. ID хранится в локальных preferences Script Toolbox и переиспользуется между запусками, чтобы aggregate unique-install и retention metrics имели смысл.

Телеметрия не должна собирать содержимое сцен, filenames, file paths, object names, scripts, Autodesk account information, OS usernames, hostnames, hardware identifiers или другие персональные/project data.

Ошибки provider никогда не должны влиять на обычную работу Script Toolbox. Доставка событий — best-effort; ошибки поглощаются facade/provider worker.

## Что отправляет Script Toolbox

После явного opt-in отправляется только заранее проверенный telemetry payload.

Каждое событие содержит:

```text
event name
distinct_id = stb-install-<random uuid>
plugin_version
build_channel
build_number
host
host_version
os
```

Некоторые события также содержат одно проверенное low-cardinality свойство:

```text
item_type
mode
share_type
```

Точный allowlist событий и свойств описан в [`TELEMETRY_EVENTS.md`](TELEMETRY_EVENTS.md).

Script Toolbox **не** помещает в event payload:

```text
scene contents
scene names
filenames
file paths
object names
item names or labels
scripts or callback code
config contents
OS usernames
hostnames
Autodesk/account data
email addresses
hardware identifiers
```

Installation identifier случайный и псевдонимный. Он нужен только для распознавания той же согласившейся установки Script Toolbox между перезапусками и не является hardware fingerprint.

### Network metadata и PostHog enrichment

Script Toolbox явно не передаёт IP пользователя или geographic location как свойства event. Однако telemetry доставляется по HTTPS, поэтому receiving service неизбежно видит source IP сетевого запроса.

PostHog может использовать эти request metadata для server-side GeoIP/enrichment полей: country, region, city, timezone, latitude/longitude или postal code. Эти поля не читаются из DCC, scene, operating-system profile или конфигурации Script Toolbox и не добавляются самим клиентом Script Toolbox.

Для текущего PostHog deployment provider-side enrichment намеренно оставлен включённым. Если privacy policy изменится, GeoIP/enrichment следует пересматривать отдельно от client payload Script Toolbox.

## Текущий PostHog provider

Официальные сборки сейчас настраивают `PostHogProvider` на EU ingestion host:

```text
https://eu.i.posthog.com
```

Публичный write-only project token PostHog не хранится в git. GitHub Actions читает `POSTHOG_PROJECT_TOKEN` из repository secrets и записывает его в `telemetry/build_config.py` непосредственно перед упаковкой Development и stable release artifacts.

В source checkout `POSTHOG_PROJECT_TOKEN` пустой, поэтому telemetry transport недоступен, если конфигурация не была stamped официальной сборкой.

Provider использует batch ingestion endpoint PostHog и отправляет данные в background daemon thread, чтобы analytics не блокировала DCC UI.

PostHog требует `distinct_id`. В официальном telemetry-enabled Runtime Script Toolbox использует сохранённый случайный installation id:

```text
stb-install-<random uuid>
```

ID создаётся только когда одновременно настроен telemetry transport и пользователь явно согласился. Он переиспользуется между сессиями Maya/Nuke/Houdini на этой установке. Если persisted installation id не удаётся сохранить, telemetry остаётся отключённой вместо молчаливого перехода на новую identity при каждом запуске.

Каждое событие принудительно содержит:

```text
$process_person_profile = false
```

поэтому Script Toolbox не создаёт PostHog person profiles. Постоянный случайный `distinct_id` используется только для последовательного подсчёта одной установки между сессиями.

## Runtime bootstrap

`script_toolbox.bootstrap.show()` инициализирует telemetry до открытия UI. Runtime-конфигурация объединяет:

- build-time provider configuration;
- сохранённый consent пользователя;
- сохранённый случайный installation id после consent;
- проверенный набор low-cardinality технических свойств.

Когда новый installation identifier создан и сохранён, Script Toolbox один раз отправляет lifecycle event:

```text
installation_created
```

Существующие установки не отправляют его повторно при последующих запусках. Обычное startup event:

```text
plugin_started
```

`plugin_started` отправляется максимум один раз на загруженный telemetry runtime и только при consent `True`.

Текущий common property allowlist:

```text
plugin_version
build_channel
build_number
host
host_version
os
```

Никакие filenames, paths, scene/object names, scripts, account information, usernames, hostnames или hardware identifiers не включаются.

## Consent и Settings UI

Когда официальная сборка имеет настроенный telemetry transport, а сохранённый consent равен `None`, после открытия Runtime Script Toolbox показывает first-run consent dialog.

Диалог предлагает два явных варианта:

- `Enable` сохраняет `True`, создаёт или переиспользует случайный installation id, немедленно включает настроенный provider и разрешает текущему runtime отправлять telemetry;
- `Don't Send` сохраняет `False` и оставляет telemetry выключенной.

Закрытие диалога без выбора оставляет consent равным `None`. Prompt показывается максимум один раз на host process, поэтому dismiss не прерывает одну и ту же сессию Maya/Nuke/Houdini повторно.

Header главного окна Script Toolbox также предоставляет `Script Toolbox Settings`. Privacy section имеет три состояния:

```text
Ask me next time
Enabled
Disabled
```

Изменение применяется сразу через `apply_telemetry_consent()`. Выключение telemetry останавливает delivery events, но не удаляет локальный случайный installation id; повторное включение продолжает использовать ту же pseudonymous identity. В том же Settings window находится preference Stable/Development update channel.

Source builds без настроенного analytics transport не показывают first-run prompt. Privacy setting остаётся доступной и consent сохраняется для будущей official build. Installation id не создаётся, пока реально не доступен transport.

## Граница provider

Конкретные backend-реализации следуют небольшому контракту `TelemetryProvider`:

```python
from script_toolbox.telemetry import TelemetryProvider


class MyAnalyticsProvider(TelemetryProvider):
    name = "my-service"

    def capture(self, event_name, properties=None):
        # Send the event to the analytics backend.
        return True
```

Регистрация и выбор provider выполняются во время application bootstrap:

```python
from script_toolbox import telemetry
from script_toolbox.core.preferences import get_telemetry_consent

provider = MyAnalyticsProvider()
telemetry.register_provider(provider)
telemetry.configure(
    provider_name="my-service",
    enabled=(get_telemetry_consent() is True),
    common_properties={
        "plugin_version": "...",
        "host": "maya",
    },
)
```

Feature-код остаётся независимым от backend и проходит через проверенный product-event gate:

```python
from script_toolbox import telemetry

telemetry.track_product_event(
    "item_created",
    {"item_type": "field"},
)
```

Поэтому переход с PostHog на собственный analytics service Script Toolbox должен требовать замены provider registration/bootstrap configuration, а не переписывания feature code или UI event instrumentation.

## Встроенный null provider

`NullTelemetryProvider` всегда зарегистрирован как `none` и является provider по умолчанию. Поэтому свежие source installs не имеют активного telemetry transport.

Null provider также служит безопасным fallback для tests, недоступных services, отсутствующей build configuration и любых сборок без analytics backend.

## Выбор provider

Provider selection относится к runtime/build configuration, а не пользовательским preferences. Это не позволяет старому сохранённому provider name закрепить пользователя за backend после смены analytics service в Script Toolbox.

Persisted privacy state содержит consent и, после opt-in, случайный installation identifier. Provider selection там не хранится.

## Дизайн событий

Телеметрия намеренно редкая. Product events отражают устойчивые действия, а не UI traffic. Текущий семантический набор:

```text
installation_created
plugin_started
item_created
item_duplicated
config_imported
config_exported
share_created
share_pasted
```

Мы намеренно не отслеживаем открытие Editor/Settings или клики Runtime items. Эти взаимодействия создавали лишний event volume без достаточной product value.

Event-specific properties ограничены low-cardinality enums:

```text
item_type
mode
share_type
```

Product/UI code использует `track_product_event()`, который отклоняет неизвестные event names, property keys и неразрешённые enum values до передачи provider. Неизвестные будущие item kinds сводятся к literal `other`, а не отправляют raw name.

Полный публичный allowlist событий/свойств находится в [`TELEMETRY_EVENTS.md`](TELEMETRY_EVENTS.md).

Нельзя отправлять произвольные strings из пользовательских сцен, скриптов, paths, labels, object names, item names, filenames или config content.

## Смена provider

Смена provider должна выполняться так:

1. Реализовать новый `TelemetryProvider`.
2. Добавить provider-specific tests.
3. Зарегистрировать его во время bootstrap.
4. Выбрать его в `telemetry.configure(...)`.
5. Сохранять event schema стабильной, пока явная product requirement не требует изменения.

Сохранённый случайный installation id не зависит от provider и должен переиспользоваться будущими analytics backends, пока consent пользователя включён. Эта граница позволяет использовать PostHog сейчас и self-hosted/custom analytics service позже без связывания backend с остальной частью плагина.
