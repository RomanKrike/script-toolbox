# Абстракция Host Callback

STEP 10 переносит подписку на DCC events за границу host abstraction.

## Публичный контракт

Хосты предоставляют три метода через `BaseHost`:

- `supports_callback(event_name)`
- `add_callback(event_name, callback)`
- `remove_callback(handle)`

Первое нормализованное событие — `selection_changed`.

`add_callback()` возвращает opaque `HostCallbackHandle` или `None`, если хост не может предоставить событие. Handles идемпотентны и могут принадлежать `HostCallbackGroup`, чтобы UI teardown освобождал все native callbacks вместе.

## Maya

`MayaHost` отображает `selection_changed` на `cmds.scriptJob(event=["SelectionChanged", callback])`.

Native scriptJob ID хранится внутри callback handle и удаляется через `cmds.scriptJob(kill=..., force=True)` во время teardown.

## Nuke

Nuke не предоставляет отдельное selection event той же формы, что Maya. `NukeHost` использует `nuke.addUpdateUI()` как native hook и хранит selection signature внутри adapter. Нормализованный callback вызывается только когда `selectedNodes()` действительно меняется. Повторные UpdateUI callbacks с тем же selection подавляются.

Wrapper callback удаляется через `nuke.removeUpdateUI()`.

## Интеграция Runtime

`ui/debounced_main_window.py` владеет `HostCallbackGroup`.

При запуске он пытается подписаться на `selection_changed`:

- подписка успешна: legacy Qt timer polling выделения каждые 300 ms останавливается;
- подписка не поддерживается или завершилась ошибкой: timer остаётся активным как compatibility fallback.

Переиспользуется существующий путь `refresh_selection_fields()`, поэтому поведение selection-backed Field и STEP 05 state-refresh scheduler сохраняют прежнюю семантику.

Все callback handles очищаются из `closeEvent()`. Hot reload уже сначала закрывает активное окно toolbox, поэтому старые host callbacks не могут удерживать предыдущий UI instance после замены модулей.

## Границы

STEP 10 не меняет:

- поведение runtime renderer registry;
- config schema или persistence;
- managed parameter-link rewriting;
- семантику editor rename/duplicate/paste;
- command history;
- control kinds.

Дополнительные host events в будущем добавляются через новый normalized event constant и его реализацию для каждого хоста без внесения Maya/Nuke API calls в UI-код.
