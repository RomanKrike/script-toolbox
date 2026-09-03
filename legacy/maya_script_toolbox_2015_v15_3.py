# -*- coding: utf-8 -*-
"""
Maya Script Toolbox - Houdini-style Interface Editor
Version 15.3
Maya 2015 / Python 2.7 / PySide 1

Main window:
    Clean runtime toolbox + gear button.

Gear -> Edit Interface:
    Left   : Create Items
    Center : Existing Interface
    Right  : Item Description / code editor
    Bottom : Apply / Accept / Cancel

Supported items:
    Section
    String
    Integer
    Float
    Checkbox
    Menu
    Color
    Button
    Label
    Separator

Button:
    Click script
    Shift+Click script
    Python / MEL

Parameter values can be read from button Python scripts:
    value = toolbox.get_value("My Float")
    value = toolbox.get_value("<item id>")

And changed:
    toolbox.set_value("My Float", 3.0)

Config:
    <Maya userPrefDir>/maya_script_toolbox.json

Compatible with configs created by previous versions.
"""

from __future__ import print_function

import copy
import io
import json
import os
import re
import sys
import traceback
import uuid

import maya.cmds as cmds
import maya.mel as mel

from PySide import QtCore
from PySide import QtGui

try:
    import shiboken
except ImportError:
    shiboken = None

try:
    from maya import OpenMayaUI as omui
except ImportError:
    omui = None


WINDOW_OBJECT_NAME = "MayaScriptToolbox2015V4"
EDITOR_OBJECT_NAME = "MayaScriptToolboxInterfaceEditor2015V4"
CONFIG_FILENAME = "maya_script_toolbox.json"

ROLE_KIND = QtCore.Qt.UserRole
ROLE_ID = QtCore.Qt.UserRole + 1

_TOOLBOX = None


try:
    text_type = unicode
except NameError:
    text_type = str

try:
    integer_type = long
except NameError:
    integer_type = int


try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


STYLE = """
/* ---------------------------------------------------------------
   Base
   --------------------------------------------------------------- */
QWidget {
    color: #d6d6d6;
    font-size: 11px;
}

QMainWindow,
QDialog {
    background-color: #292929;
}

/* Runtime Toolbox containers.
   Keep backgrounds off generic QWidget/QCheckBox so Qt4 checkbox painting
   remains native and clean. */
QWidget#ToolboxCentral {
    background-color: #2b2b2b;
}

QWidget#ToolboxContent {
    background-color: #2b2b2b;
}

QFrame#RuntimeFolder {
    background-color: #2b2b2b;
}

QWidget#RuntimeFolderContent {
    background-color: #2b2b2b;
}

/* Text labels should visually inherit the panel background. */
QLabel {
    background-color: transparent;
}

QToolTip {
    background-color: #1d1d1d;
    color: #eeeeee;
    border: 1px solid #555555;
    padding: 4px;
}

/* ---------------------------------------------------------------
   Main toolbox header
   --------------------------------------------------------------- */
QFrame#TopBar {
    background-color: #202020;
    border: 0px;
    border-bottom: 1px solid #111111;
}

QLabel#ToolboxTitle {
    background: transparent;
    color: #e2e2e2;
    font-weight: bold;
    padding-left: 4px;
}

QStatusBar {
    background-color: #232323;
    color: #8f8f8f;
    border-top: 1px solid #171717;
}

/* ---------------------------------------------------------------
   Interface editor
   --------------------------------------------------------------- */
QLabel#DialogHeading {
    background-color: #202020;
    color: #eeeeee;
    font-weight: bold;
    font-size: 12px;
    border: 1px solid #171717;
    border-radius: 3px;
    padding: 7px 9px;
}

QWidget#EditorPane {
    background-color: #303030;
    border: 1px solid #1b1b1b;
    border-radius: 3px;
}

QLabel#PaneTitle {
    background-color: transparent;
    color: #e0e0e0;
    font-weight: bold;
    padding: 2px 1px 5px 1px;
}

QLabel#HintText {
    background-color: transparent;
    color: #858585;
    font-size: 10px;
    padding: 5px 2px 1px 2px;
}

QLabel#EditorStatus {
    background-color: transparent;
    color: #8c8c8c;
    padding-left: 2px;
}

QFormLayout QLabel {
    background-color: transparent;
}

QStackedWidget#PropertyStack {
    background-color: #303030;
    border: 0px;
}

/* ---------------------------------------------------------------
   Folder headers in runtime toolbox
   --------------------------------------------------------------- */
QFrame#SectionHeader {
    background-color: #343434;
    border: 1px solid #202020;
    border-radius: 2px;
}

QLabel#SectionTitle {
    background: transparent;
    color: #dcdcdc;
    font-weight: bold;
    padding: 1px 2px;
}

/* ---------------------------------------------------------------
   Buttons
   --------------------------------------------------------------- */
QPushButton,
QToolButton {
    background-color: #3a3a3a;
    color: #dedede;
    border: 1px solid #1b1b1b;
    border-radius: 3px;
    padding: 4px 8px;
}

QPushButton {
    min-height: 20px;
}

QPushButton:hover,
QToolButton:hover {
    background-color: #464646;
    border-color: #595959;
}

QPushButton:pressed,
QToolButton:pressed {
    background-color: #2f2f2f;
    border-color: #161616;
}

QPushButton:disabled,
QToolButton:disabled {
    color: #686868;
    background-color: #303030;
    border-color: #252525;
}

QToolButton#IconButton {
    background-color: transparent;
    border: 1px solid transparent;
    padding: 2px;
}

QToolButton#IconButton:hover {
    background-color: #404040;
    border-color: #545454;
}

QToolButton#IconButton:pressed {
    background-color: #272727;
    border-color: #171717;
}

QPushButton#AcceptButton {
    background-color: #9a5826;
    border-color: #ba7139;
    color: #ffffff;
    font-weight: bold;
}

QPushButton#AcceptButton:hover {
    background-color: #ad652d;
    border-color: #d18447;
}

QPushButton#ScriptButton {
    text-align: left;
    min-height: 26px;
    padding: 4px 9px;
}

/* ---------------------------------------------------------------
   Inputs
   --------------------------------------------------------------- */
QLineEdit,
QComboBox,
QSpinBox,
QDoubleSpinBox,
QPlainTextEdit {
    background-color: #202020;
    color: #dddddd;
    border: 1px solid #151515;
    border-radius: 2px;
    selection-background-color: #8b572c;
    selection-color: #ffffff;
}

QLineEdit,
QComboBox,
QSpinBox,
QDoubleSpinBox {
    min-height: 22px;
    padding: 2px 5px;
}

QLineEdit:focus,
QComboBox:focus,
QSpinBox:focus,
QDoubleSpinBox:focus,
QPlainTextEdit:focus {
    border: 1px solid #78604a;
}

QLineEdit:disabled,
QComboBox:disabled,
QSpinBox:disabled,
QDoubleSpinBox:disabled {
    background-color: #292929;
    color: #6f6f6f;
    border-color: #242424;
}

QComboBox::drop-down {
    border: 0px;
    width: 18px;
}

QComboBox QAbstractItemView {
    background-color: #242424;
    color: #dddddd;
    border: 1px solid #151515;
    selection-background-color: #68462c;
}

/* ---------------------------------------------------------------
   Lists / trees
   --------------------------------------------------------------- */
QListWidget,
QTreeWidget {
    background-color: #242424;
    color: #d4d4d4;
    border: 1px solid #161616;
    border-radius: 2px;
    outline: 0px;
    alternate-background-color: #282828;
}

QListWidget::item,
QTreeWidget::item {
    min-height: 20px;
    padding: 3px 4px;
    border: 0px;
}

QListWidget::item:hover,
QTreeWidget::item:hover {
    background-color: #333333;
}

QListWidget::item:selected,
QTreeWidget::item:selected {
    background-color: #68462c;
    color: #ffffff;
}

QHeaderView::section {
    background-color: #303030;
    color: #a8a8a8;
    border: 0px;
    border-right: 1px solid #202020;
    border-bottom: 1px solid #171717;
    padding: 5px 6px;
    font-weight: bold;
}

/* ---------------------------------------------------------------
   Tabs
   --------------------------------------------------------------- */
QTabWidget::pane {
    background-color: #292929;
    border: 1px solid #171717;
    top: -1px;
}

QTabBar::tab {
    background-color: #303030;
    color: #aaaaaa;
    border: 1px solid #1c1c1c;
    border-bottom: 0px;
    padding: 5px 11px;
    margin-right: 1px;
}

QTabBar::tab:hover {
    background-color: #393939;
    color: #dddddd;
}

QTabBar::tab:selected {
    background-color: #414141;
    color: #f0f0f0;
    border-top: 2px solid #b46d35;
}

/* ---------------------------------------------------------------
   Group box
   --------------------------------------------------------------- */
QGroupBox {
    background-color: transparent;
    border: 1px solid #414141;
    border-radius: 3px;
    margin-top: 10px;
    padding-top: 8px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0px 5px;
    color: #bdbdbd;
}

/* ---------------------------------------------------------------
   Splitter / scroll
   --------------------------------------------------------------- */
QSplitter::handle {
    background-color: #171717;
}

QScrollArea {
    border: 0px;
    background-color: transparent;
}

QScrollArea#ToolboxScroll {
    background-color: #2b2b2b;
    border: 0px;
}

QScrollBar:vertical {
    background-color: #242424;
    width: 11px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #4a4a4a;
    min-height: 24px;
    border-radius: 4px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #5a5a5a;
}

QScrollBar:add-line:vertical,
QScrollBar:sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #242424;
    height: 11px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background-color: #4a4a4a;
    min-width: 24px;
    border-radius: 4px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #5a5a5a;
}

QScrollBar:add-line:horizontal,
QScrollBar:sub-line:horizontal {
    width: 0px;
}
"""


# ----------------------------------------------------------------------
# Programmatic toolbar icons
# ----------------------------------------------------------------------

def _icon_pixmap(size=18):
    pixmap = QtGui.QPixmap(size, size)
    pixmap.fill(QtCore.Qt.transparent)
    return pixmap


def _icon_pen(color="#d8d8d8", width=1.6):
    pen = QtGui.QPen(QtGui.QColor(color))
    pen.setWidthF(width)
    pen.setCapStyle(QtCore.Qt.RoundCap)
    pen.setJoinStyle(QtCore.Qt.RoundJoin)
    return pen


def _toolbar_icon(kind, size=18):
    """
    Draw compact monochrome toolbar icons at runtime.
    No external PNG/SVG files are required.
    Maya 2015 / Qt4 / PySide1 compatible.
    """
    pixmap = _icon_pixmap(size)
    painter = QtGui.QPainter(pixmap)

    try:
        painter.setRenderHint(
            QtGui.QPainter.Antialiasing,
            True
        )
    except Exception:
        pass

    painter.setPen(
        _icon_pen()
    )
    painter.setBrush(
        QtCore.Qt.NoBrush
    )

    w = float(size)
    h = float(size)

    if kind == "undo":
        path = QtGui.QPainterPath()
        path.moveTo(w * 0.72, h * 0.30)
        path.cubicTo(
            w * 0.48, h * 0.20,
            w * 0.28, h * 0.32,
            w * 0.28, h * 0.55
        )
        path.cubicTo(
            w * 0.28, h * 0.72,
            w * 0.43, h * 0.78,
            w * 0.60, h * 0.74
        )
        painter.drawPath(path)

        painter.setBrush(
            QtGui.QColor("#d8d8d8")
        )
        painter.drawPolygon(
            QtGui.QPolygonF([
                QtCore.QPointF(w * 0.18, h * 0.34),
                QtCore.QPointF(w * 0.38, h * 0.20),
                QtCore.QPointF(w * 0.36, h * 0.43)
            ])
        )

    elif kind == "redo":
        path = QtGui.QPainterPath()
        path.moveTo(w * 0.28, h * 0.30)
        path.cubicTo(
            w * 0.52, h * 0.20,
            w * 0.72, h * 0.32,
            w * 0.72, h * 0.55
        )
        path.cubicTo(
            w * 0.72, h * 0.72,
            w * 0.57, h * 0.78,
            w * 0.40, h * 0.74
        )
        painter.drawPath(path)

        painter.setBrush(
            QtGui.QColor("#d8d8d8")
        )
        painter.drawPolygon(
            QtGui.QPolygonF([
                QtCore.QPointF(w * 0.82, h * 0.34),
                QtCore.QPointF(w * 0.62, h * 0.20),
                QtCore.QPointF(w * 0.64, h * 0.43)
            ])
        )

    elif kind == "cut":
        painter.drawLine(
            QtCore.QPointF(w * 0.30, h * 0.23),
            QtCore.QPointF(w * 0.70, h * 0.78)
        )
        painter.drawLine(
            QtCore.QPointF(w * 0.70, h * 0.23),
            QtCore.QPointF(w * 0.30, h * 0.78)
        )
        painter.drawEllipse(
            QtCore.QRectF(
                w * 0.16, h * 0.65,
                w * 0.24, h * 0.24
            )
        )
        painter.drawEllipse(
            QtCore.QRectF(
                w * 0.60, h * 0.65,
                w * 0.24, h * 0.24
            )
        )

    elif kind == "copy":
        painter.drawRect(
            QtCore.QRectF(
                w * 0.25, h * 0.18,
                w * 0.48, h * 0.55
            )
        )
        painter.drawRect(
            QtCore.QRectF(
                w * 0.38, h * 0.32,
                w * 0.43, h * 0.52
            )
        )

    elif kind == "paste":
        painter.drawRoundedRect(
            QtCore.QRectF(
                w * 0.26, h * 0.26,
                w * 0.50, h * 0.58
            ),
            1.5,
            1.5
        )
        painter.drawRoundedRect(
            QtCore.QRectF(
                w * 0.36, h * 0.12,
                w * 0.30, h * 0.20
            ),
            2.0,
            2.0
        )

    elif kind == "find":
        painter.drawEllipse(
            QtCore.QRectF(
                w * 0.20, h * 0.18,
                w * 0.48, h * 0.48
            )
        )
        painter.drawLine(
            QtCore.QPointF(w * 0.58, h * 0.58),
            QtCore.QPointF(w * 0.82, h * 0.82)
        )

    elif kind == "find_next":
        painter.drawEllipse(
            QtCore.QRectF(
                w * 0.14, h * 0.18,
                w * 0.42, h * 0.42
            )
        )
        painter.drawLine(
            QtCore.QPointF(w * 0.48, h * 0.52),
            QtCore.QPointF(w * 0.68, h * 0.72)
        )
        painter.drawLine(
            QtCore.QPointF(w * 0.58, h * 0.79),
            QtCore.QPointF(w * 0.84, h * 0.79)
        )
        painter.drawLine(
            QtCore.QPointF(w * 0.84, h * 0.79),
            QtCore.QPointF(w * 0.74, h * 0.69)
        )
        painter.drawLine(
            QtCore.QPointF(w * 0.84, h * 0.79),
            QtCore.QPointF(w * 0.74, h * 0.89)
        )

    elif kind == "comment":
        painter.drawRoundedRect(
            QtCore.QRectF(
                w * 0.14, h * 0.20,
                w * 0.72, h * 0.48
            ),
            2.0,
            2.0
        )
        painter.drawLine(
            QtCore.QPointF(w * 0.30, h * 0.68),
            QtCore.QPointF(w * 0.23, h * 0.82)
        )
        painter.drawLine(
            QtCore.QPointF(w * 0.39, h * 0.31),
            QtCore.QPointF(w * 0.34, h * 0.57)
        )
        painter.drawLine(
            QtCore.QPointF(w * 0.59, h * 0.31),
            QtCore.QPointF(w * 0.54, h * 0.57)
        )
        painter.drawLine(
            QtCore.QPointF(w * 0.29, h * 0.40),
            QtCore.QPointF(w * 0.65, h * 0.40)
        )
        painter.drawLine(
            QtCore.QPointF(w * 0.27, h * 0.51),
            QtCore.QPointF(w * 0.63, h * 0.51)
        )

    elif kind == "uncomment":
        painter.drawRoundedRect(
            QtCore.QRectF(
                w * 0.14, h * 0.20,
                w * 0.72, h * 0.48
            ),
            2.0,
            2.0
        )
        painter.drawLine(
            QtCore.QPointF(w * 0.30, h * 0.68),
            QtCore.QPointF(w * 0.23, h * 0.82)
        )
        painter.drawLine(
            QtCore.QPointF(w * 0.25, h * 0.31),
            QtCore.QPointF(w * 0.71, h * 0.58)
        )
        painter.drawLine(
            QtCore.QPointF(w * 0.71, h * 0.31),
            QtCore.QPointF(w * 0.25, h * 0.58)
        )

    elif kind == "indent":
        painter.drawLine(
            QtCore.QPointF(w * 0.16, h * 0.28),
            QtCore.QPointF(w * 0.78, h * 0.28)
        )
        painter.drawLine(
            QtCore.QPointF(w * 0.36, h * 0.50),
            QtCore.QPointF(w * 0.78, h * 0.50)
        )
        painter.drawLine(
            QtCore.QPointF(w * 0.36, h * 0.70),
            QtCore.QPointF(w * 0.78, h * 0.70)
        )

        painter.setBrush(
            QtGui.QColor("#d8d8d8")
        )
        painter.drawPolygon(
            QtGui.QPolygonF([
                QtCore.QPointF(w * 0.14, h * 0.42),
                QtCore.QPointF(w * 0.31, h * 0.50),
                QtCore.QPointF(w * 0.14, h * 0.58)
            ])
        )

    elif kind == "unindent":
        painter.drawLine(
            QtCore.QPointF(w * 0.22, h * 0.28),
            QtCore.QPointF(w * 0.84, h * 0.28)
        )
        painter.drawLine(
            QtCore.QPointF(w * 0.22, h * 0.50),
            QtCore.QPointF(w * 0.64, h * 0.50)
        )
        painter.drawLine(
            QtCore.QPointF(w * 0.22, h * 0.70),
            QtCore.QPointF(w * 0.64, h * 0.70)
        )

        painter.setBrush(
            QtGui.QColor("#d8d8d8")
        )
        painter.drawPolygon(
            QtGui.QPolygonF([
                QtCore.QPointF(w * 0.86, h * 0.42),
                QtCore.QPointF(w * 0.69, h * 0.50),
                QtCore.QPointF(w * 0.86, h * 0.58)
            ])
        )

    elif kind == "run":
        painter.setPen(
            QtCore.Qt.NoPen
        )
        painter.setBrush(
            QtGui.QColor("#d8d8d8")
        )
        painter.drawPolygon(
            QtGui.QPolygonF([
                QtCore.QPointF(w * 0.30, h * 0.18),
                QtCore.QPointF(w * 0.80, h * 0.50),
                QtCore.QPointF(w * 0.30, h * 0.82)
            ])
        )

    elif kind == "import":
        painter.drawRect(
            QtCore.QRectF(
                w * 0.20, h * 0.58,
                w * 0.60, h * 0.22
            )
        )

        painter.drawLine(
            QtCore.QPointF(w * 0.50, h * 0.18),
            QtCore.QPointF(w * 0.50, h * 0.58)
        )

        painter.drawLine(
            QtCore.QPointF(w * 0.50, h * 0.58),
            QtCore.QPointF(w * 0.34, h * 0.42)
        )

        painter.drawLine(
            QtCore.QPointF(w * 0.50, h * 0.58),
            QtCore.QPointF(w * 0.66, h * 0.42)
        )

    elif kind == "export":
        painter.drawRect(
            QtCore.QRectF(
                w * 0.20, h * 0.58,
                w * 0.60, h * 0.22
            )
        )

        painter.drawLine(
            QtCore.QPointF(w * 0.50, h * 0.62),
            QtCore.QPointF(w * 0.50, h * 0.20)
        )

        painter.drawLine(
            QtCore.QPointF(w * 0.50, h * 0.20),
            QtCore.QPointF(w * 0.34, h * 0.36)
        )

        painter.drawLine(
            QtCore.QPointF(w * 0.50, h * 0.20),
            QtCore.QPointF(w * 0.66, h * 0.36)
        )

    elif kind == "up":
        painter.setPen(
            QtCore.Qt.NoPen
        )
        painter.setBrush(
            QtGui.QColor("#d8d8d8")
        )
        painter.drawPolygon(
            QtGui.QPolygonF([
                QtCore.QPointF(w * 0.50, h * 0.20),
                QtCore.QPointF(w * 0.20, h * 0.55),
                QtCore.QPointF(w * 0.38, h * 0.55),
                QtCore.QPointF(w * 0.38, h * 0.82),
                QtCore.QPointF(w * 0.62, h * 0.82),
                QtCore.QPointF(w * 0.62, h * 0.55),
                QtCore.QPointF(w * 0.80, h * 0.55)
            ])
        )

    elif kind == "down":
        painter.setPen(
            QtCore.Qt.NoPen
        )
        painter.setBrush(
            QtGui.QColor("#d8d8d8")
        )
        painter.drawPolygon(
            QtGui.QPolygonF([
                QtCore.QPointF(w * 0.38, h * 0.18),
                QtCore.QPointF(w * 0.62, h * 0.18),
                QtCore.QPointF(w * 0.62, h * 0.45),
                QtCore.QPointF(w * 0.80, h * 0.45),
                QtCore.QPointF(w * 0.50, h * 0.80),
                QtCore.QPointF(w * 0.20, h * 0.45),
                QtCore.QPointF(w * 0.38, h * 0.45)
            ])
        )

    elif kind == "delete":
        painter.drawRoundedRect(
            QtCore.QRectF(
                w * 0.31, h * 0.30,
                w * 0.38, h * 0.48
            ),
            1.5,
            1.5
        )
        painter.drawLine(
            QtCore.QPointF(w * 0.24, h * 0.25),
            QtCore.QPointF(w * 0.76, h * 0.25)
        )
        painter.drawLine(
            QtCore.QPointF(w * 0.40, h * 0.18),
            QtCore.QPointF(w * 0.60, h * 0.18)
        )
        painter.drawLine(
            QtCore.QPointF(w * 0.42, h * 0.40),
            QtCore.QPointF(w * 0.42, h * 0.67)
        )
        painter.drawLine(
            QtCore.QPointF(w * 0.58, h * 0.40),
            QtCore.QPointF(w * 0.58, h * 0.67)
        )

    elif kind == "clear":
        painter.drawRect(
            QtCore.QRectF(
                w * 0.30, h * 0.28,
                w * 0.40, h * 0.48
            )
        )
        painter.drawLine(
            QtCore.QPointF(w * 0.23, h * 0.23),
            QtCore.QPointF(w * 0.77, h * 0.23)
        )
        painter.drawLine(
            QtCore.QPointF(w * 0.40, h * 0.16),
            QtCore.QPointF(w * 0.60, h * 0.16)
        )

    elif kind == "reload":
        path = QtGui.QPainterPath()
        path.moveTo(w * 0.72, h * 0.33)
        path.cubicTo(
            w * 0.56, h * 0.17,
            w * 0.30, h * 0.19,
            w * 0.22, h * 0.43
        )
        path.cubicTo(
            w * 0.13, h * 0.68,
            w * 0.36, h * 0.84,
            w * 0.58, h * 0.77
        )
        painter.drawPath(path)

        painter.setBrush(
            QtGui.QColor("#d8d8d8")
        )
        painter.drawPolygon(
            QtGui.QPolygonF([
                QtCore.QPointF(w * 0.82, h * 0.30),
                QtCore.QPointF(w * 0.61, h * 0.20),
                QtCore.QPointF(w * 0.65, h * 0.43)
            ])
        )

    elif kind == "gear":
        center = QtCore.QPointF(
            w * 0.50,
            h * 0.50
        )

        painter.drawEllipse(
            QtCore.QRectF(
                w * 0.29, h * 0.29,
                w * 0.42, h * 0.42
            )
        )
        painter.drawEllipse(
            QtCore.QRectF(
                w * 0.43, h * 0.43,
                w * 0.14, h * 0.14
            )
        )

        for dx, dy in (
            (0.0, -0.36),
            (0.0, 0.36),
            (-0.36, 0.0),
            (0.36, 0.0),
            (-0.26, -0.26),
            (0.26, -0.26),
            (-0.26, 0.26),
            (0.26, 0.26)
        ):
            painter.drawLine(
                center,
                QtCore.QPointF(
                    center.x() + w * dx,
                    center.y() + h * dy
                )
            )

    painter.end()

    return QtGui.QIcon(