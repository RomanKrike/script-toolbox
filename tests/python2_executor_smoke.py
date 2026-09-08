# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import sys


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)
SCRIPTS = os.path.join(
    ROOT,
    "scripts"
)

if SCRIPTS not in sys.path:
    sys.path.insert(
        0,
        SCRIPTS
    )


from script_toolbox.core.execution_result import ExecutionResult
from script_toolbox.core.executor import evaluate_python_state_result
from script_toolbox.core.executor import execute_script
from script_toolbox.core.executor import execute_script_result


success = execute_script_result(
    "value = 2 + 2",
    context="python2:success",
    notify=False
)
assert isinstance(
    success,
    ExecutionResult
)
assert success.success is True
assert bool(success) is True
assert success.context == "python2:success"

failure = execute_script_result(
    "raise ValueError('python2 boom')",
    context="python2:failure",
    notify=False
)
assert failure.success is False
assert bool(failure) is False
assert failure.exception_type == "ValueError"
assert "python2 boom" in failure.message
assert "ValueError" in failure.traceback_text

state = evaluate_python_state_result(
    "state = True",
    notify=False
)
assert state.success is True
assert state.value is True

assert execute_script(
    "value = 1"
) is True

print(
    "Python 2 ExecutionResult smoke passed."
)
