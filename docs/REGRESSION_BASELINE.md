# Regression baseline

The regression suite protects the current Script Toolbox architecture and config schema.

## Current configuration fixtures

`tests/fixtures/current_v20_full.json` is the broad current-schema document used by editor and runtime regressions. It includes multiple folders, nested layouts, value controls, Button, Toggle Button, bindings and stable explicit IDs/names.

`tests/fixtures/golden_v20_current.json` is the compact schema-20 golden document used for load/save/idempotency checks.

The current build accepts schema 20 only.

## Editor/model invariants

The regression suite fixes these document rules:

1. top-level `sections` contain folders only;
2. `folder`, `row` and `column` are the canonical container kinds;
3. folders may contain folders, layout containers and leaf items;
4. Row/Column may nest Row/Column and leaf items but not Folder;
5. canonical traversal is depth-first and shared by indexing/reference/controller code;
6. IDs are unique stable identity; names are unique symbolic identity in editor-managed documents;
7. `label` is presentation text only;
8. subtree clone/rename rewrites managed Python references while preserving external references;
9. layout metadata survives current-schema normalization.

These model/controller regressions are Qt-independent where possible.

## Runtime invariants

Runtime regressions protect these behaviors:

- lookup by `id` and `name` targets the same item;
- `label` is not a lookup key;
- mutable values returned by `get_value()` are copies;
- Integer/Float values clamp to configured ranges through the shared numeric normalizer;
- invalid Menu values fall back to the first configured option;
- Color channels clamp to 0..1;
- Field sequences normalize to text lists;
- value edits do not change document topology, IDs or names;
- missing items and non-value items are no-ops for `store_value()`;
- runtime events execute exclusively through `bindings`;
- state behavior belongs to Toggle Button / Toggle Icon.

## CI contract

Pull requests must pass:

- Python 3.8 unit tests;
- Python 3.11 unit tests and coverage;
- flake8 correctness checks;
- package compile checks;
- Maya 2015 / Python 2.7 compile and smoke tests;
- release-package contract tests;
- downloadable test-package construction.

Architecture changes should keep these gates green unless the current contract is intentionally changed and the corresponding tests/docs are updated in the same branch.
