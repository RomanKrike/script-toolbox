# -*- coding: utf-8 -*-
from __future__ import absolute_import

from script_toolbox.core import executor
from script_toolbox.core.execution_result import ExecutionResult


class _NativeHost(object):

    def script_namespace(self):
        return {
            "host": self,
        }

    def execute_native(self, language, code):
        if code == "fail":
            raise RuntimeError("native boom")
        return "{0}:{1}".format(
            language,
            code
        )


def test_execute_script_result_python_success():
    result = executor.execute_script_result(
        "answer = 21 * 2",
        context="button:answer",
        notify=False
    )

    assert isinstance(result, ExecutionResult)
    assert result.success is True
    assert result.language == "python"
    assert result.context == "button:answer"
    assert "button:answer" in result.source_name


def test_execute_script_result_runtime_error_has_traceback():
    result = executor.execute_script_result(
        "raise ValueError('broken')",
        context="button:broken",
        notify=False
    )

    assert result.success is False
    assert result.exception_type == "ValueError"
    assert result.message == "broken"
    assert "ValueError" in result.traceback_text
    assert "button:broken" in result.traceback_text


def test_execute_script_result_syntax_error_is_structured():
    result = executor.execute_script_result(
        "if :\n    pass",
        context="button:syntax",
        notify=False
    )

    assert result.success is False
    assert result.exception_type == "SyntaxError"
    assert result.traceback_text


def test_execute_script_result_native_returns_value(monkeypatch):
    host = _NativeHost()
    monkeypatch.setattr(
        executor,
        "HOST",
        host
    )

    result = executor.execute_script_result(
        "doThing",
        language="mel",
        notify=False
    )

    assert result.success is True
    assert result.value == "mel:doThing"


def test_execute_script_result_native_failure(monkeypatch):
    host = _NativeHost()
    monkeypatch.setattr(
        executor,
        "HOST",
        host
    )

    result = executor.execute_script_result(
        "fail",
        language="mel",
        context="button:native",
        notify=False
    )

    assert result.success is False
    assert result.language == "mel"
    assert result.exception_type == "RuntimeError"
    assert result.message == "native boom"


def test_legacy_execute_script_contract_is_preserved():
    assert executor.execute_script(
        "value = 1"
    ) is True

    assert executor.execute_script(
        "raise RuntimeError('legacy')"
    ) is False


def test_state_result_and_legacy_contract():
    result = executor.evaluate_python_state_result(
        "state = 4 > 2",
        context="state:enabled",
        notify=False
    )

    assert result.success is True
    assert result.value is True
    assert result.context == "state:enabled"

    assert executor.evaluate_python_state(
        "state = False"
    ) is False


def test_state_failure_result_and_legacy_none():
    result = executor.evaluate_python_state_result(
        "raise LookupError('state failed')",
        notify=False
    )

    assert result.success is False
    assert result.exception_type == "LookupError"

    assert executor.evaluate_python_state(
        "raise LookupError('legacy state')"
    ) is None


def test_empty_code_contracts():
    script_result = executor.execute_script_result(
        "",
        notify=False
    )
    state_result = executor.evaluate_python_state_result(
        "",
        notify=False
    )

    assert script_result.success is True
    assert script_result.value is None
    assert state_result.success is True
    assert state_result.value is False
