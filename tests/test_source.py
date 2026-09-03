# -*- coding: utf-8 -*-

from script_toolbox.core.source import prepare_python_source


def test_removes_first_line_encoding_cookie():
    source = (
        u"# -*- coding: utf-8 -*-\n"
        u"value = u'тест'\n"
    )

    prepared = prepare_python_source(
        source
    )

    assert "coding:" not in prepared.splitlines()[0]
    assert prepared.splitlines()[1] == u"value = u'тест'"


def test_removes_second_line_encoding_cookie():
    source = (
        u"#!/usr/bin/env python\n"
        u"# coding=utf-8\n"
        u"print('ok')\n"
    )

    prepared = prepare_python_source(
        source
    )

    assert prepared.splitlines()[0] == "#!/usr/bin/env python"
    assert "coding=" not in prepared.splitlines()[1]
    assert prepared.count("\n") == source.count("\n")


def test_leaves_regular_comments_unchanged():
    source = (
        u"# normal comment\n"
        u"print('ok')\n"
    )

    assert prepare_python_source(
        source
    ) == source


def test_prepared_unicode_compiles():
    source = (
        u"# -*- coding: utf-8 -*-\n"
        u"value = u'тест'\n"
    )

    compile(
        prepare_python_source(
            source
        ),
        "<test>",
        "exec"
    )
