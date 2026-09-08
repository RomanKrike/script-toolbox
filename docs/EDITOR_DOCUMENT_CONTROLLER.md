# EditorDocumentController

`EditorDocumentController` is the Qt-independent owner of the Interface Editor's staged document state.

This is STEP 07 of the stabilization roadmap. It creates an application-layer boundary before command-based Undo/Redo is introduced in STEP 08.

## Responsibilities

The controller owns:

- the mutable staged document used by the Interface Editor;
- the derived `item_id -> item` cache;
- document snapshots for callers that need an isolated copy;
- internal-name collection and collision-free name allocation;
- recursive subtree cloning with fresh IDs and names;
- recursive cache registration for newly created detached tree items;
- duplicate internal-name detection.

The controller is pure Python and has no dependency on Qt, Maya, Nuke, dialogs, widgets or host APIs.

## Non-responsibilities

The controller does not own:

- JSON loading, migrations or normalization;
- persistence;
- QTreeWidget serialization or drag/drop behavior;
- property widgets;
- confirmation/error dialogs;
- Undo/Redo commands;
- runtime rendering.

Those boundaries are intentional. In particular, snapshot-based history remains in the legacy `InterfaceEditor` until STEP 08.

## Ownership contract

`EditorDocumentController(document)` makes a defensive copy of an external document. `replace()` also copies by default.

The compatibility adapter uses `adopt()` only when the legacy Qt tree has already assembled a staged document from the current item dictionaries. That preserves item object identity required by an open property editor while still transferring document ownership to the controller.

`document` is the controller-owned mutable staged document. `snapshot()` returns a deep copy.

## Cache contract

`rebuild_index()` derives the item cache from the current document using the existing depth-first `walk_items(..., include_folders=True)` traversal.

`cache_subtree()` exists for the short interval between creating/cloning a tree item and the next full tree-to-document synchronization. It recursively registers the detached subtree so legacy editor selection/property code can resolve it immediately.

## Compatibility adapter

`ui/editor_document_adapter.py` subclasses the existing Qt `InterfaceEditor` and redirects the legacy attributes and helper methods:

- `working` -> `controller.document`;
- `item_cache` -> `controller.item_cache`;
- `rebuild_cache()` -> `controller.rebuild_index()`;
- `_used_names()` -> `controller.used_names()`;
- `_unique_name()` -> `controller.unique_name()`;
- `_clone_data()` -> `controller.clone_subtree()`;
- `_cache_subtree()` -> `controller.cache_subtree()`;
- duplicate-name validation -> `controller.duplicate_name()`.

`ui/__init__.py` also updates the already-loaded `ui.interface_editor.InterfaceEditor` module attribute to the controller-backed adapter. This preserves existing direct imports while the legacy dialog is decomposed incrementally.

This compatibility layer is transitional. Future editor work should move behavior from the legacy dialog into explicit controller/command APIs rather than expanding the adapter.

## STEP 08 boundary

STEP 08 will replace deep-copy history snapshots with commands. It should use `EditorDocumentController` as the document target rather than reintroducing document ownership into Qt widgets.
