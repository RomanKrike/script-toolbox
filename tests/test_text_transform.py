# -*- coding: utf-8 -*-

from script_toolbox.core.text_transform import comment_line
from script_toolbox.core.text_transform import indent_line
from script_toolbox.core.text_transform import uncomment_line
from script_toolbox.core.text_transform import unindent_line


def test_python_comment_preserves_indent():
    assert comment_line(
        "    value = 1",
        "python"
    ) == "    # value = 1"


def test_mel_comment_preserves_indent():
    assert comment_line(
        "    setAttr foo.bar 1;",
        "mel"
    ) == "    // setAttr foo.bar 1;"


def test_uncomment_python_and_mel():
    assert uncomment_line(
        "  # value",
        "python"
    ) == "  value"

    assert uncomment_line(
        "\t// value",
        "mel"
    ) == "\tvalue"


def test_blank_line_is_not_commented():
    assert comment_line(
        "    ",
        "python"
    ) == "    "


def test_indent_and_unindent():
    assert indent_line(
        "value",
        4
    ) == "    value"

    assert unindent_line(
        "    value",
        4
    ) == "value"

    assert unindent_line(
        "\tvalue",
        4
    ) == "value"

    assert unindent_line(
        "  value",
        4
    ) == "value"
