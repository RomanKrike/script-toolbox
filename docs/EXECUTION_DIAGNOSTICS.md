# Execution diagnostics

STEP 11 introduces a structured execution result while preserving the existing
Script Toolbox script API.

## ExecutionResult

`script_toolbox.core.execution_result.ExecutionResult` contains:

- `success` / `failed`
- `value`
- `language`
- `context`
- `source_name`
- `exception_type`
- `message`
- `traceback_text`

It stores text diagnostics only. Exception and traceback objects are not kept,
so execution results do not retain Python frames or DCC objects referenced by
those frames.

`bool(result)` follows `result.success` on both Python 2.7 and Python 3.

## Structured APIs

Use these APIs when the caller needs diagnostics:

```python
from script_toolbox.core.executor import execute_script_result

result = execute_script_result(
    code,
    language="python",
    toolbox=toolbox,
    context="button:publish",
)

if not result.success:
    print(result.diagnostic_text())
```

State queries have the corresponding `evaluate_python_state_result()` API.
Successful state results carry the resolved boolean in `result.value`.

## Compatibility APIs

Existing callers continue to use:

- `execute_script()` -> `True` / `False`
- `evaluate_python_state()` -> `True` / `False` / `None` on execution failure

Their semantics are intentionally unchanged. Internally they delegate to the
structured APIs.

## Logging

Execution failures are sent through the `script_toolbox` Python logger using a
package-local `StreamHandler`. Script Toolbox does not configure or replace the
host application's root logger.

The console message contains the structured summary followed by the full
traceback. Successful execution is logged only at debug level and is filtered
by the default Script Toolbox handler.

The error dialog contains a concise summary and directs the user to the host
Script Editor / console for the complete traceback.

## Context

The optional `context` argument is intended for stable identifiers such as:

- `button:publish`
- `on_change:quality`
- `state:viewport_mode`

It is also embedded in the compiled Python source name, so Python tracebacks can
identify the Script Toolbox operation that produced the error.

Adding richer item-specific context throughout the UI can now be done
incrementally without changing the result/error contract.

## Python 2.7

The result object, logger setup and executor APIs remain Python 2.7 compatible.
CI executes a dedicated Python 2.7 smoke test for success, failure, traceback,
boolean conversion and state-query behavior.
