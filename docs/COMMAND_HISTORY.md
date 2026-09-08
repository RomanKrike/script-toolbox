# Command-based Interface Editor history

STEP 08 replaces the active Interface Editor's full-document snapshot history with reversible commands bound to `EditorDocumentController`.

## Goals

The previous implementation stored deep copies of the entire staged config in the undo and redo stacks. Large toolboxes therefore multiplied scripts, labels, values and nested structures by the history depth.

The command history keeps the existing user-facing behavior while reducing history payloads to the affected state.

## Command model

`core/editor_commands.py` provides:

- `CommandHistory` — bounded undo/redo stacks with a default limit of 100 commands;
- `ItemStateCommand` — before/after state for one parameter, excluding structural `items` children;
- `DocumentDeltaCommand` — ID-only before/after topology plus payloads only for added/removed subtrees and before/after states only for common items whose properties changed;
- `DocumentCapture` — a temporary pre-change capture used to build a delta;
- `build_document_delta()` — converts the pre-change capture and current controller state into a reversible command.

Commands are Qt-independent and Python 2.7 compatible.

## Structural history

Create, Paste, Duplicate, Delete, toolbar Move and drag/drop reorder all flow through the same topology delta path.

Topology contains only:

- ordered root item IDs;
- ordered child IDs for Folder and Row containers.

Unchanged item payloads are not copied into structural commands.

For an insert, the command stores only the inserted subtree payload. For a delete, it stores only the removed subtree payload. Pure move/reorder commands need no subtree payload at all.

## Property coalescing

The existing 300 ms single-shot history timer is retained.

Property widgets mutate their bound item immediately, but repeated `changed` signals within the timer window produce one `ItemStateCommand`. The command stores only that item's non-structural before/after state.

Changing selection flushes a pending property command first, preserving the existing edit boundary.

## Import

Import is captured as a document delta. Replace Toolbox can naturally contain large removed/added subtree payloads because the operation itself replaces the document, but unchanged common IDs still do not require whole-document snapshots.

Append and Insert imports normally store only their newly added subtrees and topology.

## Apply

The controller-backed adapter implements Apply directly instead of calling the legacy snapshot bookkeeping path.

Apply:

1. synchronizes the Qt tree into the staged controller;
2. validates names;
3. copies the staged document to runtime config;
4. saves and rebuilds runtime UI;
5. re-seeds `EditorDocumentController` from the applied runtime config.

Existing command objects remain usable after Apply because stable item IDs are preserved.

## Selection restoration

Every command records `selection_before` and `selection_after` where available. Undo/Redo rebuilds the editor tree and restores the matching item when it still exists.

## Compatibility boundary

`ui/editor_document_adapter.py` remains the bridge to the current monolithic Qt dialog. It overrides active history behavior while leaving the old methods in `ui/interface_editor.py` as dormant compatibility code.

Future editor decomposition should call command/controller APIs directly rather than adding new snapshot paths.

## Out of scope

STEP 08 does not introduce:

- runtime renderer registry;
- host callback abstraction;
- JSON schema changes;
- persistence changes;
- Qt test harness changes.
