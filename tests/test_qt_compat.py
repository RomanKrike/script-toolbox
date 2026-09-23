# -*- coding: utf-8 -*-
from __future__ import print_function

import sys

from script_toolbox.qt_compat import PYSIDE
from script_toolbox.qt_compat import PYSIDE2
from script_toolbox.qt_compat import PYSIDE6
from script_toolbox.qt_compat import binding_candidates
from script_toolbox.qt_compat import install_legacy_api
from script_toolbox.qt_compat import mirror_widgets_onto_qtgui
from script_toolbox.qt_compat import version_major


_BINDING_MODULES = (
    "PySide",
    "PySide.QtCore",
    "PySide.QtGui",
    "PySide2",
    "PySide2.QtCore",
    "PySide2.QtGui",
    "PySide2.QtWidgets",
    "PySide6",
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
)


def _clear_loaded_bindings(monkeypatch):
    for name in _BINDING_MODULES:
        monkeypatch.delitem(
            sys.modules,
            name,
            raising=False
        )


def test_version_major_extracts_dcc_major_version():
    assert version_major("2025") == 2025
    assert version_major("16.0v1") == 16
    assert version_major("20.5.550") == 20
    assert version_major(" 21.0.123") == 21
    assert version_major(2019) == 2019
    assert version_major("") == 0
    assert version_major("unknown") == 0


def test_maya_binding_generations(monkeypatch):
    _clear_loaded_bindings(
        monkeypatch
    )

    assert binding_candidates(
        "maya",
        "2015"
    )[0] == PYSIDE
    assert binding_candidates(
        "maya",
        "2016"
    )[0] == PYSIDE
    assert binding_candidates(
        "maya",
        "2017"
    )[0] == PYSIDE2
    assert binding_candidates(
        "maya",
        "2024"
    )[0] == PYSIDE2
    assert binding_candidates(
        "maya",
        "2025"
    )[0] == PYSIDE6
    assert binding_candidates(
        "maya",
        "2026"
    )[0] == PYSIDE6


def test_nuke_binding_generations(monkeypatch):
    _clear_loaded_bindings(
        monkeypatch
    )

    assert binding_candidates(
        "nuke",
        "12.2v10"
    )[0] == PYSIDE2
    assert binding_candidates(
        "nuke",
        "15.1v4"
    )[0] == PYSIDE2
    assert binding_candidates(
        "nuke",
        "16.0v1"
    )[0] == PYSIDE6
    assert binding_candidates(
        "nuke",
        "17.0v1"
    )[0] == PYSIDE6


def test_houdini_binding_generations(monkeypatch):
    _clear_loaded_bindings(
        monkeypatch
    )

    assert binding_candidates(
        "houdini",
        "19.0.720"
    )[0] == PYSIDE2
    assert binding_candidates(
        "houdini",
        "20.5.550"
    )[0] == PYSIDE2
    assert binding_candidates(
        "houdini",
        "21.0.440"
    )[0] == PYSIDE6
    assert binding_candidates(
        "houdini",
        "22.0.100"
    )[0] == PYSIDE6


def test_houdini_preferred_binding_can_select_optional_qt6(monkeypatch):
    _clear_loaded_bindings(
        monkeypatch
    )

    assert binding_candidates(
        "houdini",
        "20.5.550",
        preferred_binding="PySide6"
    )[0] == PYSIDE6


def test_houdini_21_preferred_binding_can_select_qt5_variant(monkeypatch):
    _clear_loaded_bindings(
        monkeypatch
    )

    assert binding_candidates(
        "houdini",
        "21.0.440",
        preferred_binding="PySide2"
    )[0] == PYSIDE2


def test_loaded_binding_takes_precedence_over_version_guess(monkeypatch):
    _clear_loaded_bindings(
        monkeypatch
    )
    monkeypatch.setitem(
        sys.modules,
        "PySide2",
        object()
    )

    assert binding_candidates(
        "maya",
        "2025"
    )[0] == PYSIDE2


def test_mirror_widgets_preserves_existing_qtgui_attributes():
    class QtGuiFake(object):
        ExistingWidget = "gui-version"

    class QtWidgetsFake(object):
        ExistingWidget = "widgets-version"
        NewWidget = "new-widget"

    result = mirror_widgets_onto_qtgui(
        QtGuiFake,
        QtWidgetsFake
    )

    assert result is QtGuiFake
    assert QtGuiFake.ExistingWidget == "gui-version"
    assert QtGuiFake.NewWidget == "new-widget"


def test_install_legacy_api_adds_qt6_method_aliases():
    class QMenu(object):
        def exec(self):
            return "menu"

    class QFontMetrics(object):
        def horizontalAdvance(
            self,
            text
        ):
            return len(
                text
            )

    class QtCoreFake(object):
        pass

    class QtGuiFake(object):
        pass

    QtGuiFake.QMenu = QMenu
    QtGuiFake.QFontMetrics = QFontMetrics

    install_legacy_api(
        QtCoreFake,
        QtGuiFake,
        None
    )

    assert QMenu().exec_() == "menu"
    assert QFontMetrics().width("abcd") == 4


def test_install_legacy_api_adapts_qregular_expression_subset():
    class Match(object):
        def __init__(
            self,
            start,
            length
        ):
            self._start = start
            self._length = length

        def hasMatch(self):
            return self._start >= 0

        def capturedStart(self):
            return self._start

        def capturedLength(self):
            return self._length

    class Iterator(object):
        def __init__(
            self,
            match
        ):
            self._match = match
            self._used = False

        def hasNext(self):
            return (
                not self._used and
                self._match.hasMatch()
            )

        def next(self):
            self._used = True
            return self._match

    class QRegularExpression(object):
        def __init__(
            self,
            pattern
        ):
            self.pattern = pattern

        def globalMatch(
            self,
            text,
            offset=0
        ):
            needle = self.pattern
            start = text.find(
                needle,
                offset
            )
            length = (
                len(needle)
                if start >= 0
                else -1
            )
            return Iterator(
                Match(
                    start,
                    length
                )
            )

    class QtCoreFake(object):
        pass

    class QtGuiFake(object):
        pass

    QtCoreFake.QRegularExpression = QRegularExpression

    install_legacy_api(
        QtCoreFake,
        QtGuiFake,
        None
    )

    expression = QtCoreFake.QRegExp(
        "abc"
    )
    assert expression.indexIn(
        "--abc--"
    ) == 2
    assert expression.matchedLength() == 3
    assert expression.indexIn(
        "--abc--",
        3
    ) == -1
    assert expression.matchedLength() == -1
