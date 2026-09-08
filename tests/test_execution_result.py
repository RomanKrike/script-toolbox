# -*- coding: utf-8 -*-
from __future__ import absolute_import

import io
import logging

from script_toolbox.core.execution_result import ExecutionResult
from script_toolbox.core.logging_utils import get_logger
from script_toolbox.core.logging_utils import log_execution_result


def test_execution_result_success_contract():
    result = ExecutionResult(
        True,
        value=42,
        language="python",
        context="button:build"
    )

    assert result.success is True
    assert result.failed is False
    assert bool(result) is True
    assert result.value == 42
    assert "button:build" in result.summary()
    assert "python" in result.summary()


def test_execution_result_failure_diagnostic_text():
    result = ExecutionResult(
        False,
        language="mel",
        context="button:test",
        exception_type="RuntimeError",
        message="boom",
        traceback_text="Traceback line"
    )

    assert result.failed is True
    assert bool(result) is False
    assert "RuntimeError: boom" in result.summary()
    assert "Traceback line" in result.diagnostic_text()


def test_script_toolbox_logger_installs_one_handler():
    logger = get_logger()
    first = [
        handler
        for handler in logger.handlers
        if getattr(handler, "_script_toolbox_handler", False)
    ]

    get_logger()
    second = [
        handler
        for handler in logger.handlers
        if getattr(handler, "_script_toolbox_handler", False)
    ]

    assert len(first) == 1
    assert len(second) == 1
    assert logger.propagate is False


def test_failure_is_logged_at_error_level():
    stream = io.StringIO()
    handler = logging.StreamHandler(
        stream
    )
    logger = logging.getLogger(
        "script_toolbox_test_capture"
    )
    logger.handlers = [
        handler
    ]
    logger.propagate = False
    logger.setLevel(
        logging.DEBUG
    )

    result = ExecutionResult(
        False,
        context="test",
        exception_type="ValueError",
        message="bad value"
    )

    log_execution_result(
        result,
        logger=logger
    )
    handler.flush()

    assert "ValueError: bad value" in stream.getvalue()
