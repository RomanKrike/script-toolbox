# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

from ..pycompat import text_type


class ExecutionResult(object):
    """Serializable result of executing Script Toolbox code.

    The result intentionally stores text diagnostics instead of exception or
    traceback objects so it never keeps execution frames/DCC objects alive.
    """

    def __init__(
        self,
        success,
        value=None,
        language="python",
        context="",
        source_name="",
        exception_type="",
        message="",
        traceback_text=""
    ):
        self.success = bool(success)
        self.value = value
        self.language = text_type(language or "python")
        self.context = text_type(context or "")
        self.source_name = text_type(source_name or "")
        self.exception_type = text_type(exception_type or "")
        self.message = text_type(message or "")
        self.traceback_text = text_type(traceback_text or "")

    def __nonzero__(self):
        return self.success

    def __bool__(self):
        return self.success

    @property
    def failed(self):
        return not self.success

    def summary(self):
        if self.success:
            if self.context:
                return "{0} succeeded ({1}).".format(
                    self.context,
                    self.language
                )
            return "Script succeeded ({0}).".format(
                self.language
            )

        error = self.exception_type or "ExecutionError"
        if self.message:
            error = "{0}: {1}".format(
                error,
                self.message
            )

        if self.context:
            return "{0} failed ({1}): {2}".format(
                self.context,
                self.language,
                error
            )

        return "Script failed ({0}): {1}".format(
            self.language,
            error
        )

    def diagnostic_text(self):
        summary = self.summary()
        if not self.traceback_text:
            return summary
        return "{0}\n{1}".format(
            summary,
            self.traceback_text.rstrip()
        )


__all__ = [
    "ExecutionResult",
]
