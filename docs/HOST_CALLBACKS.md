# Host Callback Abstraction

STEP 10 moves DCC event subscription behind the host boundary.

## Public contract

Hosts expose three methods through `BaseHost`:

- `supports_callback(event_name)`
- `add_callback(event_name, callback)`
- `remove_callback(handle)`

The first normalized event is `selection_changed`.

`add_callback()` returns an opaque `HostCallbackHandle` or `None` when the host cannot provide the event. Handles are idempotent and can be owned by `HostCallbackGroup` so UI teardown can release every native callback together.

## Maya

`MayaHost` maps `selection_changed` to `cmds.scriptJob(event=["SelectionChanged", callback])`.

The native scriptJob ID is stored inside the callback handle and removed with `cmds.scriptJob(kill=..., force=True)` during teardown.

## Nuke

Nuke does not expose the same dedicated selection event shape as Maya. `NukeHost` uses `nuke.addUpdateUI()` as the native hook and keeps a selection signature inside the adapter. The normalized callback is emitted only when `selectedNodes()` actually changes. Duplicate UpdateUI callbacks with the same selection are suppressed.

The wrapper callback is removed through `nuke.removeUpdateUI()`.

## Runtime integration

`ui/debounced_main_window.py` owns a `HostCallbackGroup`.

At startup it attempts to subscribe to `selection_changed`:

- successful subscription: the legacy 300 ms Qt selection polling timer is stopped;
- unsupported/failed subscription: the timer remains active as a compatibility fallback.

The existing `refresh_selection_fields()` path is reused, so selection-backed Field behavior and the STEP 05 state-refresh scheduler keep the same semantics.

All callback handles are cleared from `closeEvent()`. Hot reload already closes the active toolbox window first, so old host callbacks cannot retain the previous UI instance after module replacement.

## Boundaries

STEP 10 does not change:

- runtime renderer registry behavior;
- config schema or persistence;
- managed parameter-link rewriting;
- editor rename/duplicate/paste semantics;
- command history;
- control kinds.

Additional host events can be added later by defining another normalized event constant and implementing it per host without introducing Maya/Nuke API calls into UI code.
