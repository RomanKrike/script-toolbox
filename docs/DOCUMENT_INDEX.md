# Document lookup index

Script Toolbox runtime value lookups use a cached `DocumentIndex` instead of traversing the full toolbox document for every `find_item`, `get_value`, or `store_value` call.

## Lookup contract

Identity lookup is strictly:

```text
id -> name
```

`id` is the stable internal identifier. `name` is the supported symbolic key used by scripts and public value APIs. `label` is presentation text only and never participates in lookup.

For duplicate names, the first item in canonical `walk_items()` traversal order wins. IDs are expected to be unique.

Folders are excluded from the normal runtime value index because they do not expose runtime values.

## Runtime cache

`core.values.get_document_index(document)` keeps a small identity-based LRU cache. Replacing a normalized config dictionary naturally creates a new index.

The cache retains at most eight document objects. Stable successful lookups are O(1). On an index miss, the value layer can perform one canonical linear traversal to detect in-place structural/name changes and then rebuild the index.

## In-place mutations

Normal runtime value edits only change `value` fields and do not invalidate lookup keys.

Editor structural operations rebuild or replace the index through `EditorDocumentController`. If external code mutates `name` or document structure directly, a subsequent miss can self-heal through canonical traversal.

For explicit invalidation:

```python
from script_toolbox.core.values import invalidate_document_index

invalidate_document_index(toolbox.config)
```

The next lookup rebuilds the index.

## Explicit index use

Core callers can pass a `DocumentIndex` explicitly:

```python
from script_toolbox.model import DocumentIndex
from script_toolbox.core.values import get_value

index = DocumentIndex(document)
value = get_value(document, "render_mode", index=index)
```

The default API uses the cached index automatically.
