# State Refresh Scheduler

State buttons can evaluate arbitrary Python through `state_get_script`. A full refresh therefore has cost proportional to the number and complexity of state buttons.

Before STEP 05, every runtime value change and every relevant selection update called `refresh_state_buttons()` synchronously. A burst from a spin box, menu, field, or selection-driven control could repeatedly execute every registered state getter.

## Scheduling contract

The active runtime now separates two concepts:

- `refresh_state_buttons()` — explicit, synchronous full refresh;
- `request_state_refresh()` — coalesced refresh request for high-frequency producers.

Runtime value changes and selection polling use the scheduled path. Explicit callers and runtime rebuilds keep synchronous behavior.

## Coalescing window

`STATE_REFRESH_INTERVAL_MS` is 100 ms.

The scheduler is throttle/coalesce rather than trailing-edge debounce. The first request opens one 100 ms window. Additional requests while that window is pending are merged into the same refresh and do not restart the timer.

This caps continuous full state evaluation to approximately 10 passes per second while keeping state indicators responsive during long interactions such as dragging a numeric control.

## Rebuild behavior

A runtime rebuild must show correct state immediately after widgets are created. Selection refresh performed inside `rebuild()` therefore does not enqueue a second pass. The rebuild ends with one synchronous full state refresh.

A direct external call to `toolbox.refresh_state_buttons()` also remains synchronous. If a scheduled pass is already pending, that pending pass is cancelled before the explicit refresh to prevent duplicate work.

## StateRefreshQueue

`core/state_refresh.py` contains a host-independent `StateRefreshQueue` with no Qt dependency. It tracks whether one full refresh is already pending:

- `request()` returns `True` only for the first request in a window;
- `consume()` clears and consumes the pending request;
- `cancel()` clears a pending request without executing it.

The Qt `QTimer` remains in the runtime window and runs on the Maya/Nuke UI thread.

## Deliberate non-goals

STEP 05 does not infer dependencies between individual state buttons and values. Every scheduled pass still refreshes all registered state buttons. Selective dependency tracking, host event callbacks, and per-item invalidation remain later optimizations.
