# -*- coding: utf-8 -*-
from __future__ import print_function

import re


def comment_line(
    line,
    language="python"
):
    if not line.strip():
        return line

    marker = (
        "// "
        if language == "mel"
        else "# "
    )

    match = re.match(
        r"^(\s*)",
        line
    )
    indent = match.group(1)

    return (
        indent +
        marker +
        line[len(indent):]
    )


def uncomment_line(
    line,
    language="python"
):
    marker = (
        "//"
        if language == "mel"
        else "#"
    )

    match = re.match(
        r"^(\s*)" +
        re.escape(marker) +
        r"\s?",
        line
    )

    if not match:
        return line

    return (
        line[:len(match.group(1))] +
        line[match.end():]
    )


def indent_line(
    line,
    width=4
):
    return (
        " " * int(width)
    ) + line


def unindent_line(
    line,
    width=4
):
    width = max(
        1,
        int(width)
    )

    spaces = " " * width

    if line.startswith(
        spaces
    ):
        return line[
            width:
        ]

    if line.startswith(
        "\t"
    ):
        return line[
            1:
        ]

    leading_spaces = (
        len(line) -
        len(line.lstrip(" "))
    )

    return line[
        min(
            width,
            leading_spaces
        ):
    ]


__all__ = [
    "comment_line",
    "indent_line",
    "uncomment_line",
    "unindent_line",
]
