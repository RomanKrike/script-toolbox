# ConfigStore and debounced runtime persistence

Script Toolbox runtime values can emit many change events in a short period. Integer/Float spin boxes are the main example: dragging or stepping a value may produce a sequence of `valueChanged` signals.

Before STEP 04, every changed value called `save_config()` immediately. Because configuration writes serialize the whole toolbox document, flush it, `fsync()` it, rotate backups, and atomically replace the primary JSON, a short interaction could generate many full disk writes.

## Persistence contract

`core/config_store.py` owns the host-independent persistence state:

- the currently bound document;
- whether that document is dirty;
- the configured writer/path;
- synchronous `flush()` and explicit `save()` behavior;
- dirty state remains set when a write fails.

`ConfigStore` intentionally owns no worker thread and no Qt object.

The active Maya/Nuke runtime uses a single-shot `QTimer` on the DCC main thread with a 500 ms interval. Runtime `store_value()` changes mark the store dirty and restart that timer. A burst of value events therefore collapses into one config write after interaction settles.

## Immediate saves

The public `toolbox.save()` behavior remains synchronous. Interface Editor Apply/Accept and other explicit callers therefore keep the previous durability contract.

Only persistence originating from runtime `store_value()` uses the debounce path.

## Mandatory flush points

Pending changes are flushed before:

1. config reload;
2. development module reload;
3. updater installation starts;
4. updater hot reload;
5. toolbox/window close.

If a mandatory flush fails, the `ConfigStore` remains dirty. Close/reload/update transitions are stopped where possible instead of silently discarding the pending in-memory values.

Timer-triggered write failures are reported in the status bar and remain retryable on the next change or explicit lifecycle flush.

## DCC/threading rule

Do not move config persistence to a background Python thread merely to reduce UI stalls. Maya 2015/Python 2.7 and Nuke host lifecycles make background teardown/error handling harder, while backup and replace operations are already short bounded filesystem transactions.

The current design reduces write frequency while keeping persistence on the DCC main thread. A later split between toolbox definition and per-user runtime state can reduce serialization size further without changing this debounce contract.

## Config schema migrations

`core.config_schema` now owns a sequential migration registry in addition to current-schema validation. Production migration functions are registered by their source version and must advance exactly one step (`N -> N+1`). `CONFIG_VERSION` remains `20`; no artificial schema bump was introduced for the framework itself.

Load behavior is intentionally strict:

- current-schema documents are validated and copied without migration;
- older documents are migrated only when every required step is registered;
- a missing step aborts with an explicit schema error;
- documents newer than the running build are rejected and never downgraded;
- migration functions receive a copy, must return a dictionary with exactly the next version, and remain independent of Qt/DCC APIs;
- migrated output is validated again as the current schema before normalization.

Migration during `load_config()` is in-memory only. The source file is not overwritten merely because it was migrated successfully. If the migrated document is later saved through the normal `save_config()` path, the existing atomic-write/backup machinery validates the source, rotates the raw pre-save file into `.bak1`, and only then replaces the primary config. No second migration-specific backup system is maintained.
