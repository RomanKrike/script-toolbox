# EditorDocumentController

`EditorDocumentController` is the Qt-independent owner of the Interface Editor's staged document state.

## Responsibilities

The controller owns:

- the mutable staged document used by the Interface Editor;
- the derived `item_id -> item` cache;
- isolated document snapshots;
- internal-name collection and collision-free name allocation;
- recursive subtree cloning with fresh IDs and names;
- managed reference rewriting during rename/clone;
- recursive cache registration for detached tree items;
- topology capture and restoration;
- duplicate internal-name detection.

The controller is pure Python and has no dependency on Qt, Maya, Nuke, dialogs, widgets or host APIs.

## Container contract

Structural recursion uses the model-owned container predicate. `folder`, `row` and `column` are therefore handled consistently by cache, clone, topology and reference operations.

The controller does not duplicate a private Folder/Row traversal rule. Canonical traversal belongs to the model.

## Non-responsibilities

The controller does not own:

- JSON file I/O or schema validation;
- persistence;
- QTreeWidget serialization or drag/drop behavior;
- property widgets;
- confirmation/error dialogs;
- runtime rendering.

Undo/Redo commands live in `core.editor_commands` and target this controller rather than owning separate document snapshots in Qt widgets.

## Ownership contract

`EditorDocumentController(document)` makes a defensive copy of an external document. `replace()` also copies by default.

`adopt()` is used when the Interface Editor has assembled the staged document from the currently managed item dictionaries and object identity must be preserved for an open property editor.

`document` is the controller-owned mutable staged document. `snapshot()` returns a deep copy.

## Cache and identity

`rebuild_index()` derives the item cache from canonical `walk_items(..., include_folders=True)` traversal.

`cache_subtree()` covers the short interval between creating/cloning a detached tree item and the next full tree-to-document synchronization.

Stable identity is `id`. `name` is the supported symbolic script identifier. `label` is not identity.

## Interface Editor integration

`ui/editor_document_adapter.py` composes controller ownership, command history, layout helpers, view-state preservation, search presentation and sharing into the active Interface Editor class.

The active adapter routes document operations through `EditorDocumentController`, including name allocation, clone, cache, duplicate-name validation, topology and reference updates. Row/Column tree behavior is supplied by helper functions in `ui/layout_editor_adapter.py`; there is no separate layout document controller.

The generated editor class is marked only so development hot reload can avoid stacking the same active adapter repeatedly. That marker is a reload implementation detail, not a historical document/runtime compatibility API.

## Reference rewrite contract

Reference rewriting is deliberately conservative. The supported automatic form is a direct managed Script Toolbox API call with a literal first argument, for example:

```python
toolbox.get_value("source_value")
toolbox.set_value("source_value", value)
```

The method must be one of `core.references.REFERENCE_METHODS`. Rename and subtree duplication keep the existing source-only/changed-ID helpers for compatibility, while structured `*_result` helpers additionally report unresolved references.

The unresolved detector recognizes a small set of high-confidence risks that are intentionally not rewritten, including direct aliases (`tb = toolbox; tb.get_value("old")`), a managed call through a simple string variable, and simple computed string arguments. It does not treat comments or unrelated string literals as runtime references. It is not a general Python data-flow/refactoring engine.

When rename or Duplicate leaves unresolved references, the Interface Editor completes the safe document operation and shows a non-modal status warning listing affected items where possible. The user should review those scripts manually. Supported literal references are still rewritten automatically in the same operation.

## Behavioral-test boundary

Critical editor behavior is tested at the Qt-independent controller/command boundary where possible: semantic Undo/Redo deltas, rename rewriting, subtree duplication, and no-op history behavior execute the same model/controller code used by the UI. Runtime toggle transitions and renderer-hook idempotency are also exposed through Qt-independent helpers so CI does not require `pytest-qt` or a DCC-host Qt binding.
