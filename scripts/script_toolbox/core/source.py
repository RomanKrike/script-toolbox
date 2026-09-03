# -*- coding: utf-8 -*-
from __future__ import print_function

import re

from ..pycompat import text_type


_ENCODING_COOKIE = re.compile(
    r"^[ \t\f]*#.*?coding[:=][ \t]*[-_.A-Za-z0-9]+"
)


def prepare_python_source(
    code
):
    """
    Prepare editor/config source for compile() across Python 2 and 3.

    Script Toolbox stores button/editor text as Unicode. Python 2 rejects an
    encoding declaration inside a Unicode source object with:

        SyntaxError: encoding declaration in Unicode string

    Encoding cookies are only meaningful when Python decodes byte source, so
    remove a cookie from the first or second physical line while preserving
    the line count for tracebacks.
    """
    if code is None:
        return ""

    if not isinstance(
        code,
        text_type
    ):
        return code

    lines = code.splitlines(
        True
    )

    for index in range(
        min(
            2,
            len(
                lines
            )
        )
    ):
        line = lines[
            index
        ]
        content = line.rstrip(
            "\r\n"
        )
        newline = line[
            len(
                content
            ):
        ]

        if _ENCODING_COOKIE.match(
            content
        ):
            lines[
                index
            ] = (
                "# encoding handled by Script Toolbox" +
                newline
            )

    return "".join(
        lines
    )


__all__ = [
    "prepare_python_source",
]
