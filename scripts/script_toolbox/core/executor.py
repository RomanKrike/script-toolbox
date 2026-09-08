# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

import traceback

from ..hosts import HOST
from ..pycompat import text_type
from .execution_result import ExecutionResult
from .logging_utils import get_logger
from .logging_utils import log_execution_result
from .source import prepare_python_source


LOGGER = get_logger()


def _script_namespace(toolbox=None, extra_namespace=None):
    namespace = {
        "__name__": "__script_toolbox_button__",
        "toolbox": toolbox,
    }
    namespace.update(
        HOST.script_namespace()
    )

    if extra_namespace:
        namespace.update(
            extra_namespace
        )

    return namespace


def _source_name(
    default_name,
    context
):
    context = text_type(
        context or ""
    ).strip()
    if not context:
        return default_name
    return "{0} {1}>".format(
        default_name[:-1],
        context
    )


def _failure_result(
    exc,
    language,
    context,
    source_name
):
    return ExecutionResult(
        False,
        value=None,
        language=language,
        context=context,
        source_name=source_name,
        exception_type=exc.__class__.__name__,
        message=text_type(exc),
        traceback_text=traceback.format_exc()
    )


def _notify_failure(
    result,
    parent=None,
    title="Script Toolbox"
):
    try:
        from ..compat import QtGui

        QtGui.QMessageBox.critical(
            parent,
            title,
            (
                "{0}\n\n"
                "See the host Script Editor / console for the full traceback."
            ).format(
                result.summary()
            )
        )
    except Exception as exc:
        LOGGER.debug(
            "Could not show execution error dialog: %s",
            text_type(exc)
        )


def execute_script_result(
    code,
    language="python",
    toolbox=None,
    parent=None,
    extra_namespace=None,
    context="",
    notify=True
):
    """Execute code and return a structured :class:`ExecutionResult`."""
    code = code or ""
    language = (
        language or "python"
    ).lower()
    context = text_type(
        context or ""
    )
    source_name = _source_name(
        "<Script Toolbox>",
        context
    )

    if not code.strip():
        return ExecutionResult(
            True,
            value=None,
            language=language,
            context=context,
            source_name=source_name
        )

    try:
        value = None

        if language == "python":
            namespace = _script_namespace(
                toolbox=toolbox,
                extra_namespace=extra_namespace
            )

            compiled = compile(
                prepare_python_source(
                    code
                ),
                source_name,
                "exec"
            )
            eval(
                compiled,
                namespace,
                namespace
            )

        else:
            value = HOST.execute_native(
                language,
                code
            )

        result = ExecutionResult(
            True,
            value=value,
            language=language,
            context=context,
            source_name=source_name
        )
        log_execution_result(
            result,
            logger=LOGGER
        )
        return result

    except Exception as exc:
        result = _failure_result(
            exc,
            language,
            context,
            source_name
        )
        log_execution_result(
            result,
            logger=LOGGER
        )

        if notify:
            _notify_failure(
                result,
                parent=parent
            )

        return result


def execute_script(
    code,
    language="python",
    toolbox=None,
    parent=None,
    extra_namespace=None,
    context=""
):
    """Compatibility wrapper returning the historical ``True``/``False``."""
    return bool(
        execute_script_result(
            code,
            language=language,
            toolbox=toolbox,
            parent=parent,
            extra_namespace=extra_namespace,
            context=context,
            notify=True
        ).success
    )


def evaluate_python_state_result(
    code,
    toolbox=None,
    parent=None,
    context="",
    notify=True
):
    """Execute a state query and return a structured ExecutionResult."""
    code = code or ""
    context = text_type(
        context or ""
    )
    source_name = _source_name(
        "<Script Toolbox State>",
        context
    )

    if not code.strip():
        return ExecutionResult(
            True,
            value=False,
            language="python",
            context=context,
            source_name=source_name
        )

    namespace = _script_namespace(
        toolbox=toolbox,
        extra_namespace={
            "state": False,
        }
    )

    try:
        compiled = compile(
            prepare_python_source(
                code
            ),
            source_name,
            "exec"
        )
        eval(
            compiled,
            namespace,
            namespace
        )

        result = ExecutionResult(
            True,
            value=bool(
                namespace.get(
                    "state",
                    False
                )
            ),
            language="python",
            context=context,
            source_name=source_name
        )
        log_execution_result(
            result,
            logger=LOGGER
        )
        return result

    except Exception as exc:
        result = _failure_result(
            exc,
            "python",
            context,
            source_name
        )
        log_execution_result(
            result,
            logger=LOGGER
        )

        if notify:
            _notify_failure(
                result,
                parent=parent,
                title="Script Toolbox State"
            )

        return result


def evaluate_python_state(
    code,
    toolbox=None,
    parent=None,
    context=""
):
    """Compatibility wrapper preserving the historical bool/None contract."""
    result = evaluate_python_state_result(
        code,
        toolbox=toolbox,
        parent=parent,
        context=context,
        notify=True
    )

    if not result.success:
        return None

    return bool(
        result.value
    )


__all__ = [
    "ExecutionResult",
    "evaluate_python_state",
    "evaluate_python_state_result",
    "execute_script",
    "execute_script_result",
]
