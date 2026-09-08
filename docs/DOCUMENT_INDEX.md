# Document lookup index

Script Toolbox runtime value lookups use a cached `DocumentIndex` instead of traversing the full toolbox document for every `find_item`, `get_value`, or `store_value` call.

## Lookup contract

The index preserves the existing public lookup order:

```text
id -> name -> label
```

For duplicate values within one lookup field, the first item in `walk_items()` traversal order wins, matching the previous linear implementation.

Folders are excluded from the runtime value index, matching the previous `find_item(..., include_folders=False)` behavior.

## Runtime cache

`core.values.get_document_index(document)` keeps a small identity-based LRU cache. The current runtime/editor architecture replaces the normalized config dictionary when a config is reloaded or Interface Editor changes are applied, so a replacement document naturally receives a new index.

The cache retains at most eight document objects. This prevents repeated editor/reload documents from accumulating indefinitely while keeping the hot runtime document indexed.

Stable successful lookups are O(1). A missing lookup may still perform the legacy linear scan as a compatibility fallback.

## In-place mutations

Normal runtime value edits only change item `value` fields and do not invalidate lookup keys.

External scripts may still modify `name`, `label`, or document structure directly. The lookup layer handles common in-place additions and key changes by falling back to a linear scan on an index miss and rebuilding the index when the item is found. Stale direct key entries are rejected before they are returned.

For larger structural edits or reordering of duplicate names/labels, explicitly invalidate the index:

```python
from script_toolbox.core.values import invalidate_document_index

invalidate_document_index(toolbox.config)
```

The next value lookup rebuilds the index from the current document.

## Explicit index use

Core callers can also pass a `DocumentIndex` explicitly:

```python
from script_toolbox.model import DocumentIndex
from script_toolbox.core.values import get_value

index = DocumentIndex(document)
value = get_value(document, "render_mode", index=index)
```

The existing API remains compatible when no explicit index is supplied.
