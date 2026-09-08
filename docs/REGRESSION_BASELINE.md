# Regression baseline

STEP 06 establishes a behavioral baseline before the Interface Editor and runtime renderer refactors.

The goal is to make future architecture changes prove that they preserve user-visible configuration semantics rather than relying only on unit tests for individual helpers.

## Golden configuration fixtures

`tests/fixtures/golden_v16_full.json` is the current-schema reference document. It intentionally includes:

- multiple root folders;
- nested folders;
- a Row container;
- action and state buttons;
- String, Integer, Float, Checkbox, Menu, Color and Field values;
- Label and Separator layout items;
- selection-backed fields;
- scripts, state labels/colors and layout metadata;
- stable explicit IDs and names.

`tests/fixtures/golden_v15_legacy.json` is the legacy-schema reference. It covers the v15 -> v16 migration path plus legacy Toggle conversion and normalization of historical values.

Golden tests verify that load/save/load is idempotent after migration and normalization. A future schema migration may intentionally change the normalized result, but such a change must update the migration and the golden expectation together.

## Editor/model invariants

The regression suite fixes the following current editor document rules:

1. top-level `sections` contain folders only;
2. folders may contain nested folders, rows and leaf items;
3. rows may contain leaf controls/actions only, never folders or rows;
4. traversal order is stable and depth-first;
5. IDs and names in the golden document are unique;
6. folder type and row layout metadata survive normalization.

These tests are deliberately Qt-independent. They protect the document contract that `InterfaceEditor.sync_working_from_tree()` currently produces, allowing STEP 07 to refactor editor ownership without requiring a Maya/PySide1 test harness first.

## Runtime value invariants

Runtime regressions fix the current value API behavior:

- lookup by ID, name and label resolves the same item;
- mutable values returned by `get_value()` are copies;
- Integer/Float values clamp to configured ranges;
- invalid Menu values fall back to the first menu item;
- Color channels clamp to 0..1;
- Field sequences normalize to text lists;
- value edits do not alter document topology, IDs or names;
- missing items and non-value items are no-ops for `store_value()`.

## CI contract

The normal Python 3.8 and 3.11 test jobs run all regression tests automatically. Production package code is not changed by STEP 06, so the existing Python 2.7 compile/smoke and release-package gates remain the compatibility check for this step.

When STEP 07 or later refactors change editor/runtime architecture, these tests should remain green unless a behavior change is intentional and documented.
