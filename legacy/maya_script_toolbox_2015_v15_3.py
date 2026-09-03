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

    return QtGui.QIcon(        pixmap
    )


# ----------------------------------------------------------------------
# General helpers
# ----------------------------------------------------------------------

def maya_main_window():
    if omui is None or shiboken is None:
        return None

    try:
        pointer = omui.MQtUtil.mainWindow()

        if not pointer:
            return None

        return shiboken.wrapInstance(
            integer_type(pointer),
            QtGui.QWidget
        )
    except Exception:
        return None


def _new_id():
    return uuid.uuid4().hex


def _config_path():
    try:
        folder = cmds.internalVar(userPrefDir=True)
    except Exception:
        folder = os.path.expanduser("~")

    return os.path.normpath(
        os.path.join(folder, CONFIG_FILENAME)
    )


def _clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def _safe_float(value, fallback=0.0):
    try:
        return float(value)
    except Exception:
        return float(fallback)


def _safe_int(value, fallback=0):
    try:
        return int(value)
    except Exception:
        return int(fallback)


def _safe_color(value):
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        value = [0.25, 0.25, 0.25]

    return [
        _clamp(_safe_float(value[0], 0.25), 0.0, 1.0),
        _clamp(_safe_float(value[1], 0.25), 0.0, 1.0),
        _clamp(_safe_float(value[2], 0.25), 0.0, 1.0)
    ]


def _sanitize_internal_name(value, fallback="item"):
    """
    Houdini-style internal Name:
    - intended for scripts
    - letters, numbers and underscores
    - cannot start with a number
    """
    value = text_type(value or "").strip()

    if not value:
        value = text_type(fallback or "item")

    value = re.sub(r"[^A-Za-z0-9_]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")

    if not value:
        value = "item"

    if value[0].isdigit():
        value = "_" + value

    return value


def _default_internal_name(kind, item_id):
    return _sanitize_internal_name(
        "{0}_{1}".format(
            kind,
            text_type(item_id)[:4]
        ),
        kind
    )


def _safe_menu_items(value):
    if isinstance(value, (list, tuple)):
        result = [
            text_type(item)
            for item in value
            if text_type(item).strip()
        ]
    else:
        text = text_type(value or "")
        result = [
            line.strip()
            for line in text.replace(",", "\n").splitlines()
            if line.strip()
        ]

    if not result:
        result = ["Option 1", "Option 2"]

    return result


# ----------------------------------------------------------------------
# Item factories + migration
# ----------------------------------------------------------------------

def _base_item(kind, data=None, default_name=None):
    data = data or {}

    item_id = data.get("id") or _new_id()
    default_label = default_name or kind.title()

    # Migration:
    # Older Toolbox versions only had "name", which was visible text.
    # Preserve that text as Label and create a script-safe internal Name.
    legacy_name = data.get("name")
    label = data.get("label")

    if label is None:
        label = legacy_name or default_label

    if legacy_name:
        internal_name = _sanitize_internal_name(
            legacy_name,
            kind
        )
    else:
        internal_name = _default_internal_name(
            kind,
            item_id
        )

    return {
        "kind": kind,
        "id": item_id,
        "name": internal_name,
        "label": text_type(label),
        "show_label": bool(
            data.get(
                "show_label",
                True
            )
        ),
        "tooltip": data.get("tooltip") or ""
    }


def _button_item(data=None):
    data = data or {}
    item = _base_item(
        "button",
        data,
        "New Button"
    )

    language = str(
        data.get("language", "python")
    ).lower()

    if language not in ("python", "mel"):
        language = "python"

    item.update({
        "language": language,
        "click_script": data.get("click_script") or "",
        "shift_script": data.get("shift_script") or "",
        "color": _safe_color(
            data.get("color", [0.25, 0.25, 0.25])
        )
    })

    return item


def _string_item(data=None):
    data = data or {}
    item = _base_item(
        "string",
        data,
        "String"
    )
    item["value"] = text_type(
        data.get("value", "")
    )
    return item


def _integer_item(data=None):
    data = data or {}
    item = _base_item(
        "integer",
        data,
        "Integer"
    )

    minimum = _safe_int(
        data.get("min", -1000000),
        -1000000
    )
    maximum = _safe_int(
        data.get("max", 1000000),
        1000000
    )

    if minimum > maximum:
        minimum, maximum = maximum, minimum

    item.update({
        "min": minimum,
        "max": maximum,
        "step": max(
            1,
            _safe_int(
                data.get("step", 1),
                1
            )
        ),
        "value": _clamp(
            _safe_int(
                data.get("value", 0),
                0
            ),
            minimum,
            maximum
        )
    })

    return item


def _float_item(data=None):
    data = data or {}
    item = _base_item(
        "float",
        data,
        "Float"
    )

    minimum = _safe_float(
        data.get("min", -1000000.0),
        -1000000.0
    )
    maximum = _safe_float(
        data.get("max", 1000000.0),
        1000000.0
    )

    if minimum > maximum:
        minimum, maximum = maximum, minimum

    item.update({
        "min": minimum,
        "max": maximum,
        "step": max(
            0.000001,
            _safe_float(
                data.get("step", 0.1),
                0.1
            )
        ),
        "decimals": _clamp(
            _safe_int(
                data.get("decimals", 3),
                3
            ),
            0,
            8
        ),
        "value": _clamp(
            _safe_float(
                data.get("value", 0.0),
                0.0
            ),
            minimum,
            maximum
        )
    })

    return item


def _toggle_item(data=None):
    """
    Legacy migration helper.

    Old Toggle items are converted to Checkbox items with the label on
    the left, preserving the old visual layout.
    """
    migrated = dict(
        data or {}
    )

    if not migrated.get(
        "label_position"
    ):
        migrated[
            "label_position"
        ] = "left"

    return _checkbox_item(
        migrated
    )


def _checkbox_item(data=None):
    """
    Boolean checkbox parameter.

    label_position:
        left  - Label | [x]
        right - [x] | Label
    """
    data = data or {}

    item = _base_item(
        "checkbox",
        data,
        "Checkbox"
    )

    label_position = text_type(
        data.get(
            "label_position",
            "right"
        )
    ).lower()

    if label_position not in (
        "left",
        "right"
    ):
        label_position = "right"

    item["value"] = bool(
        data.get(
            "value",
            False
        )
    )
    item["label_position"] = label_position

    return item


def _menu_item(data=None):
    data = data or {}
    item = _base_item(
        "menu",
        data,
        "Menu"
    )

    choices = _safe_menu_items(
        data.get(
            "items",
            ["Option 1", "Option 2"]
        )
    )

    value = text_type(
        data.get(
            "value",
            choices[0]
        )
    )

    if value not in choices:
        value = choices[0]

    item["items"] = choices
    item["value"] = value
    return item


def _color_item(data=None):
    data = data or {}
    item = _base_item(
        "color",
        data,
        "Color"
    )
    item["value"] = _safe_color(
        data.get(
            "value",
            [0.5, 0.5, 0.5]
        )
    )
    return item


def _field_item(data=None):
    """
    Read-only display field.

    source:
        value     - value is set manually or from a button/script
        selection - automatically mirrors current Maya selection
    """
    data = data or {}

    item = _base_item(
        "field",
        data,
        "Field"
    )

    source = text_type(
        data.get(
            "source",
            "value"
        )
    ).lower()

    if source not in (
        "value",
        "selection"
    ):
        source = "value"

    value = data.get(
        "value",
        ""
    )

    if isinstance(
        value,
        tuple
    ):
        value = list(
            value
        )

    item.update({
        "source": source,
        "value": value,
        "placeholder": text_type(
            data.get(
                "placeholder",
                ""
            )
        ),
        "selectable": bool(
            data.get(
                "selectable",
                True
            )
        ),
        "select_scene": bool(
            data.get(
                "select_scene",
                False
            )
        ),
        "multiple": bool(
            data.get(
                "multiple",
                True
            )
        ),
        "long_names": bool(
            data.get(
                "long_names",
                False
            )
        )
    })

    return item


def _label_item(data=None):
    data = data or {}
    return _base_item(
        "label",
        data,
        "Label"
    )


def _separator_item(data=None):
    data = data or {}
    item = _base_item(
        "separator",
        data,
        "Separator"
    )
    item.pop("tooltip", None)
    return item


def _row_item(data=None):
    """
    Technical horizontal layout container.
    Row can contain normal interface items but cannot contain
    Section or another Row.
    """
    data = data or {}

    item = _base_item(
        "row",
        data,
        "Row"
    )

    children = []

    for raw_child in data.get("items", []) or []:
        if not isinstance(raw_child, dict):
            continue

        child_kind = raw_child.get(
            "kind",
            "button"
        )

        if child_kind in (
            "section",
            "folder",
            "row"
        ):
            continue

        children.append(
            _new_item_by_kind(
                child_kind,
                raw_child
            )
        )

    item["items"] = children
    item["spacing"] = max(
        0,
        min(
            30,
            _safe_int(
                data.get(
                    "spacing",
                    4
                ),
                4
            )
        )
    )

    return item


def _folder_item(data=None):
    """
    Nested Folder item.

    Top-level folders are still stored in config["sections"] for backward
    compatibility. Nested folders use the same data structure plus kind=folder.
    """
    item = _section(
        data or {}
    )
    item["kind"] = "folder"
    return item


def _new_item_by_kind(kind, data=None):
    if kind == "folder":
        return _folder_item(data)
    if kind == "row":
        return _row_item(data)
    if kind == "field":
        return _field_item(data)
    if kind == "string":
        return _string_item(data)
    if kind == "integer":
        return _integer_item(data)
    if kind == "float":
        return _float_item(data)
    if kind == "toggle":
        return _toggle_item(data)
    if kind == "checkbox":
        return _checkbox_item(data)
    if kind == "menu":
        return _menu_item(data)
    if kind == "color":
        return _color_item(data)
    if kind == "label":
        return _label_item(data)
    if kind == "separator":
        return _separator_item(data)

    return _button_item(data)


def _section(data=None):
    data = data or {}

    raw_items = data.get("items")

    # Migration from previous versions.
    if raw_items is None:
        raw_items = data.get("buttons", [])

    items = []

    for raw_item in raw_items or []:
        if not isinstance(raw_item, dict):
            continue

        kind = raw_item.get(
            "kind",
            "button"
        )

        items.append(
            _new_item_by_kind(
                kind,
                raw_item
            )
        )

    section_id = data.get("id") or _new_id()

    legacy_name = data.get("name")
    label = data.get("label")

    if label is None:
        label = legacy_name or "Folder"

    if legacy_name:
        internal_name = _sanitize_internal_name(
            legacy_name,
            "folder"
        )
    else:
        internal_name = _default_internal_name(
            "folder",
            section_id
        )

    folder_type = text_type(
        data.get(
            "folder_type",
            "collapsible"
        )
    ).lower()

    if folder_type not in (
        "collapsible",
        "simple",
        "tabs",
        "radio"
    ):
        folder_type = "collapsible"

    return {
        "id": section_id,
        "name": internal_name,
        "label": text_type(label),
        "show_label": bool(
            data.get(
                "show_label",
                True
            )
        ),
        "folder_type": folder_type,
        "collapsed": bool(
            data.get("collapsed", False)
        ),
        "items": items
    }


def _default_config():
    return {
        "version": 15,
        "sections": [
            _section({
                "name": "my_tools",
                "label": "My Tools"
            })
        ]
    }


def normalize_config(data):
    if not isinstance(data, dict):
        return _default_config()

    raw_sections = data.get("sections")

    if not isinstance(raw_sections, list):
        return _default_config()

    sections = []

    for raw_section in raw_sections:
        if isinstance(raw_section, dict):
            sections.append(
                _section(raw_section)
            )

    if not sections:
        sections = _default_config()["sections"]

    return {
        "version": 15,
        "sections": sections
    }


def load_config():
    path = _config_path()

    if not os.path.isfile(path):
        return _default_config()

    try:
        with io.open(
            path,
            "r",
            encoding="utf-8"
        ) as handle:
            return normalize_config(
                json.load(handle)
            )

    except Exception as exc:
        cmds.warning(
            "Script Toolbox: failed to load config: {0}".format(
                exc
            )
        )
        return _default_config()


def save_config(config):
    path = _config_path()
    folder = os.path.dirname(path)

    try:
        if folder and not os.path.isdir(folder):
            os.makedirs(folder)

        payload = json.dumps(
            config,
            ensure_ascii=False,
            indent=2
        )

        if not isinstance(
            payload,
            text_type
        ):
            payload = payload.decode(
                "utf-8"
            )

        with io.open(
            path,
            "w",
            encoding="utf-8"
        ) as handle:
            handle.write(payload)

        return True

    except Exception as exc:
        cmds.warning(
            "Script Toolbox: failed to save config: {0}".format(
                exc
            )
        )
        return False


# ----------------------------------------------------------------------
# Script execution
# ----------------------------------------------------------------------

def _shift_pressed():
    try:
        return bool(
            cmds.getModifiers() & 1
        )
    except Exception:
        return False


def execute_script(
    code,
    language,
    parent=None,
    toolbox=None
):
    if not code or not code.strip():
        return True

    try:
        if str(language).lower() == "mel":
            mel.eval(code)

        else:
            namespace = {
                "__name__": "__maya_script_toolbox_button__",
                "cmds": cmds,
                "mel": mel,
                "toolbox": toolbox
            }

            compiled = compile(
                code,
                "<Maya Script Toolbox>",
                "exec"
            )

            eval(
                compiled,
                namespace,
                namespace
            )

        return True

    except Exception:
        error_text = traceback.format_exc()
        print(error_text)

        box = QtGui.QMessageBox(parent)
        box.setWindowTitle(
            "Script Error"
        )
        box.setIcon(
            QtGui.QMessageBox.Critical
        )
        box.setText(
            "The script raised an error."
        )
        box.setDetailedText(
            error_text
        )
        box.exec_()

        return False


# ----------------------------------------------------------------------
# Code editor
# ----------------------------------------------------------------------

class LineNumberArea(QtGui.QWidget):

    def __init__(self, editor):
        QtGui.QWidget.__init__(
            self,
            editor
        )
        self.editor = editor

    def sizeHint(self):
        return QtCore.QSize(
            self.editor.line_number_area_width(),
            0
        )

    def paintEvent(self, event):
        self.editor.paint_line_numbers(
            event
        )


class CodeEditor(QtGui.QPlainTextEdit):

    def __init__(self, parent=None):
        QtGui.QPlainTextEdit.__init__(
            self,
            parent
        )

        self.line_numbers = LineNumberArea(
            self
        )

        font = QtGui.QFont(
            "Consolas"
        )
        font.setStyleHint(
            QtGui.QFont.Monospace
        )
        font.setPointSize(10)
        self.setFont(font)

        try:
            self.setTabStopWidth(
                self.fontMetrics().width(" ") * 4
            )
        except Exception:
            pass

        self.setLineWrapMode(
            QtGui.QPlainTextEdit.NoWrap
        )

        self.blockCountChanged.connect(
            self.update_margin
        )
        self.updateRequest.connect(
            self.update_line_numbers
        )
        self.cursorPositionChanged.connect(
            self.highlight_line
        )

        self.update_margin()
        self.highlight_line()

    def line_number_area_width(self):
        digits = len(
            str(
                max(
                    1,
                    self.blockCount()
                )
            )
        )

        return 10 + (
            self.fontMetrics().width("9") *
            digits
        )

    def update_margin(self, *args):
        self.setViewportMargins(
            self.line_number_area_width(),
            0,
            0,
            0
        )

    def update_line_numbers(
        self,
        rect,
        dy
    ):
        if dy:
            self.line_numbers.scroll(
                0,
                dy
            )
        else:
            self.line_numbers.update(
                0,
                rect.y(),
                self.line_numbers.width(),
                rect.height()
            )

        if rect.contains(
            self.viewport().rect()
        ):
            self.update_margin()

    def resizeEvent(self, event):
        QtGui.QPlainTextEdit.resizeEvent(
            self,
            event
        )

        rect = self.contentsRect()

        self.line_numbers.setGeometry(
            QtCore.QRect(
                rect.left(),
                rect.top(),
                self.line_number_area_width(),
                rect.height()
            )
        )

    def paint_line_numbers(
        self,        event
    ):
        painter = QtGui.QPainter(
            self.line_numbers
        )

        painter.fillRect(
            event.rect(),
            QtGui.QColor("#252525")
        )

        painter.setPen(
            QtGui.QColor("#777777")
        )

        block = self.firstVisibleBlock()
        number = block.blockNumber()

        top = int(
            self.blockBoundingGeometry(block)
            .translated(
                self.contentOffset()
            )
            .top()
        )

        bottom = top + int(
            self.blockBoundingRect(
                block
            ).height()
        )

        while (
            block.isValid() and
            top <= event.rect().bottom()
        ):
            if (
                block.isVisible() and
                bottom >= event.rect().top()
            ):
                painter.drawText(
                    0,
                    top,
                    self.line_numbers.width() - 5,
                    self.fontMetrics().height(),
                    QtCore.Qt.AlignRight,
                    str(number + 1)
                )

            block = block.next()
            top = bottom
            bottom = top + int(
                self.blockBoundingRect(
                    block
                ).height()
            )
            number += 1

    def highlight_line(self):
        selection = QtGui.QTextEdit.ExtraSelection()

        selection.format.setBackground(
            QtGui.QColor("#303030")
        )

        selection.format.setProperty(
            QtGui.QTextFormat.FullWidthSelection,
            True
        )

        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()

        self.setExtraSelections(
            [selection]
        )


class ScriptHighlighter(QtGui.QSyntaxHighlighter):

    PYTHON_WORDS = [
        "and", "as", "assert", "break", "class",
        "continue", "def", "del", "elif", "else",
        "except", "exec", "finally", "for", "from",
        "global", "if", "import", "in", "is",
        "lambda", "not", "or", "pass", "print",
        "raise", "return", "try", "while", "with",
        "yield", "True", "False", "None"
    ]

    MEL_WORDS = [
        "if", "else", "for", "while", "switch",
        "case", "break", "continue", "return",
        "global", "proc", "string", "int", "float",
        "vector", "matrix"
    ]

    def __init__(
        self,
        document,
        language="python"
    ):
        QtGui.QSyntaxHighlighter.__init__(
            self,
            document
        )

        self.language = language
        self.rules = []
        self.rebuild()

    def _fmt(
        self,
        color,
        bold=False,
        italic=False
    ):
        result = QtGui.QTextCharFormat()
        result.setForeground(
            QtGui.QColor(color)
        )

        if bold:
            result.setFontWeight(
                QtGui.QFont.Bold
            )

        result.setFontItalic(
            italic
        )
        return result

    def set_language(
        self,
        language
    ):
        self.language = language
        self.rebuild()

    def rebuild(self):
        self.rules = []

        keyword_fmt = self._fmt(
            "#d4a15d",
            bold=True
        )
        string_fmt = self._fmt(
            "#b9c66b"
        )
        comment_fmt = self._fmt(
            "#757575",
            italic=True
        )
        number_fmt = self._fmt(
            "#79a8d7"
        )
        maya_fmt = self._fmt(
            "#69b5b5"
        )

        words = (
            self.MEL_WORDS
            if self.language == "mel"
            else self.PYTHON_WORDS
        )

        for word in words:
            self.rules.append((
                QtCore.QRegExp(
                    "\\b{0}\\b".format(
                        word
                    )
                ),
                keyword_fmt
            ))

        self.rules.append((
            QtCore.QRegExp(
                "\"[^\"\\n]*\""
            ),
            string_fmt
        ))

        self.rules.append((
            QtCore.QRegExp(
                "'[^'\\n]*'"
            ),
            string_fmt
        ))

        if self.language == "mel":
            self.rules.append((
                QtCore.QRegExp(
                    "//[^\\n]*"
                ),
                comment_fmt
            ))
        else:
            self.rules.append((
                QtCore.QRegExp(
                    "#[^\\n]*"
                ),
                comment_fmt
            ))

            for word in (
                "cmds",
                "mel",
                "toolbox"
            ):
                self.rules.append((
                    QtCore.QRegExp(
                        "\\b{0}\\b".format(
                            word
                        )
                    ),
                    maya_fmt
                ))

        self.rules.append((
            QtCore.QRegExp(
                "\\b[0-9]+(?:\\.[0-9]+)?\\b"
            ),
            number_fmt
        ))

        self.rehighlight()

    def highlightBlock(
        self,
        text
    ):
        for expression, fmt in self.rules:
            index = expression.indexIn(
                text
            )

            while index >= 0:
                length = expression.matchedLength()

                self.setFormat(
                    index,
                    length,
                    fmt
                )

                index = expression.indexIn(
                    text,
                    index + max(
                        1,
                        length
                    )
                )


# ----------------------------------------------------------------------
# Runtime display field
# ----------------------------------------------------------------------

class DisplayField(QtGui.QLineEdit):

    def __init__(
        self,
        toolbox,
        item,
        parent=None
    ):
        QtGui.QLineEdit.__init__(
            self,
            parent
        )

        self.toolbox = toolbox
        self.item_id = item["id"]
        self.selectable = bool(
            item.get(
                "selectable",
                True
            )
        )
        self.select_scene = bool(
            item.get(
                "select_scene",
                False
            )
        )

        self.setReadOnly(
            True
        )

        try:
            self.setPlaceholderText(
                item.get(
                    "placeholder",
                    ""
                )
            )
        except Exception:
            pass

        if not self.selectable:
            self.setFocusPolicy(
                QtCore.Qt.NoFocus
            )

        self.setToolTip(
            item.get(
                "tooltip",
                ""
            )
        )

        self.refresh()

    def refresh(self):
        self.setText(
            self.toolbox.field_display_text(
                self.item_id
            )
        )

        if not self.selectable:
            self.deselect()

    def mousePressEvent(self, event):
        if self.selectable:
            QtGui.QLineEdit.mousePressEvent(
                self,
                event
            )
        else:
            event.accept()

    def mouseMoveEvent(self, event):
        if self.selectable:
            QtGui.QLineEdit.mouseMoveEvent(
                self,
                event
            )
        else:
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if self.select_scene:
            self.toolbox.select_field_objects(
                self.item_id
            )

        if self.selectable:
            QtGui.QLineEdit.mouseDoubleClickEvent(
                self,
                event
            )
        else:
            event.accept()


# ----------------------------------------------------------------------
# Runtime interface
# ----------------------------------------------------------------------

class RuntimeSection(QtGui.QFrame):
    """
    Runtime Folder renderer.

    Internal class name is kept for compatibility with older versions.
    """

    def __init__(
        self,
        toolbox,
        section,
        parent=None,
        embedded=False
    ):
        QtGui.QFrame.__init__(
            self,
            parent
        )
        self.setObjectName(
            "RuntimeFolder"
        )

        self.toolbox = toolbox
        self.section = section
        self.embedded = bool(
            embedded
        )
        self.folder_type = section.get(
            "folder_type",
            "collapsible"
        )

        root = QtGui.QVBoxLayout(
            self
        )
        root.setContentsMargins(
            0,
            0,
            0,
            4
        )
        root.setSpacing(
            3
        )

        self.arrow = None
        self.header = None

        # Tabs / Radio pages are embedded and do not draw another header.
        if not self.embedded:
            self.header = QtGui.QFrame()
            self.header.setObjectName(
                "SectionHeader"
            )

            header_layout = QtGui.QHBoxLayout(
                self.header
            )
            header_layout.setContentsMargins(
                4,
                2,
                4,
                2
            )
            header_layout.setSpacing(
                3
            )

            if self.folder_type == "collapsible":
                self.arrow = QtGui.QToolButton()
                self.arrow.setFixedWidth(
                    19
                )
                self.arrow.clicked.connect(
                    self.toggle
                )
                header_layout.addWidget(
                    self.arrow
                )

            title = QtGui.QLabel(
                section.get(
                    "label",
                    section["name"]
                )
                if section.get(
                    "show_label",
                    True
                )
                else ""
            )
            title.setObjectName(
                "SectionTitle"
            )

            header_layout.addWidget(
                title
            )
            header_layout.addStretch(
                1
            )

            # Simple folders keep a header but have no collapse arrow.
            root.addWidget(
                self.header
            )

        self.content = QtGui.QWidget()
        self.content.setObjectName(
            "RuntimeFolderContent"
        )
        self.content_layout = QtGui.QVBoxLayout(
            self.content
        )
        self.content_layout.setContentsMargins(
            4,
            2,
            4,
            2
        )
        self.content_layout.setSpacing(
            3
        )

        self._populate_runtime_items(
            section["items"]
        )

        root.addWidget(
            self.content
        )

        self.update_state()

    def _populate_runtime_items(
        self,
        items
    ):
        """
        Populate this Folder recursively.

        Consecutive nested folders of type Tabs or Radio Buttons are grouped
        inside their current parent Folder, just like at the top level.
        """
        index = 0

        while index < len(
            items
        ):
            item = items[
                index
            ]

            if item.get(
                "kind"
            ) == "folder":
                folder_type = item.get(
                    "folder_type",
                    "collapsible"
                )

                if folder_type in (
                    "tabs",
                    "radio"
                ):
                    group = [
                        item
                    ]
                    index += 1

                    while index < len(
                        items
                    ):
                        candidate = items[
                            index
                        ]

                        if (
                            candidate.get(
                                "kind"
                            ) != "folder" or
                            candidate.get(
                                "folder_type",
                                "collapsible"
                            ) != folder_type
                        ):
                            break

                        group.append(
                            candidate
                        )
                        index += 1

                    if folder_type == "tabs":
                        widget = RuntimeFolderTabs(
                            self.toolbox,
                            group,
                            self.content
                        )
                    else:
                        widget = RuntimeFolderRadio(
                            self.toolbox,
                            group,
                            self.content
                        )

                else:
                    widget = RuntimeSection(
                        self.toolbox,
                        item,
                        self.content
                    )
                    index += 1

            else:
                widget = self.build_runtime_widget(
                    item,
                    compact=False
                )
                index += 1

            if widget is not None:
                self.content_layout.addWidget(
                    widget
                )


    # ------------------------------------------------------------------
    # Runtime controls
    # ------------------------------------------------------------------

    def _label(self, item):
        if not item.get(
            "show_label",
            True
        ):
            return ""

        return item.get(
            "label",
            item.get(
                "name",
                ""
            )
        )

    def _tooltip(self, item):
        return item.get(
            "tooltip",
            ""
        )

    def _parameter_container(
        self,
        item,
        compact=False
    ):
        widget = QtGui.QWidget()
        layout = QtGui.QHBoxLayout(
            widget
        )
        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )
        layout.setSpacing(4)

        label_text = self._label(
            item
        )

        if label_text:
            label = QtGui.QLabel(
                label_text
            )

            if not compact:
                label.setMinimumWidth(
                    105
                )

            layout.addWidget(
                label
            )

        widget.setToolTip(
            self._tooltip(
                item
            )
        )

        return widget, layout

    def _button_widget(
        self,
        item
    ):
        button = QtGui.QPushButton(
            self._label(
                item
            )
        )
        button.setObjectName(
            "ScriptButton"
        )
        button.setToolTip(
            self._tooltip(
                item
            )
        )

        rgb = [
            int(value * 255)
            for value in item.get(
                "color",
                [0.25, 0.25, 0.25]
            )
        ]

        button.setStyleSheet(
            "QPushButton#ScriptButton {"
            "background-color: rgb(%d,%d,%d);"
            "}" % (
                rgb[0],
                rgb[1],
                rgb[2]
            )
        )

        button.clicked.connect(
            lambda checked=False, item_id=item["id"]:
            self.toolbox.run_item(
                item_id
            )
        )

        return button

    def _toggle_widget(
        self,
        item,
        compact=False
    ):
        container, layout = self._parameter_container(
            item,
            compact=compact
        )

        checkbox = QtGui.QCheckBox()

        checkbox.setToolTip(
            self._tooltip(
                item
            )
        )

        checkbox.setChecked(
            bool(
                item.get(
                    "value",
                    False
                )
            )
        )

        checkbox.toggled.connect(
            lambda value, item_id=item["id"]:
            self.toolbox.store_value(
                item_id,
                bool(value)
            )
        )

        layout.addWidget(
            checkbox,
            0
        )

        return container

    def _checkbox_widget(
        self,
        item,
        compact=False
    ):
        label_position = item.get(
            "label_position",
            "right"
        )

        if label_position == "left":
            container, layout = self._parameter_container(
                item,
                compact=compact
            )

            checkbox = QtGui.QCheckBox()
            checkbox.setToolTip(
                self._tooltip(
                    item
                )
            )
            checkbox.setChecked(
                bool(
                    item.get(
                        "value",
                        False
                    )
                )
            )
            checkbox.toggled.connect(
                lambda value, item_id=item["id"]:
                self.toolbox.store_value(
                    item_id,
                    bool(value)
                )
            )

            layout.addWidget(
                checkbox,
                0
            )

            return container

        checkbox = QtGui.QCheckBox(
            self._label(
                item
            )
        )

        checkbox.setToolTip(
            self._tooltip(
                item
            )
        )

        checkbox.setChecked(
            bool(
                item.get(
                    "value",
                    False
                )
            )
        )

        checkbox.toggled.connect(
            lambda value, item_id=item["id"]:
            self.toolbox.store_value(
                item_id,
                bool(value)
            )
        )

        return checkbox

    def _color_button_style(
        self,
        button,
        color
    ):
        rgb = [
            int(value * 255)
            for value in _safe_color(
                color
            )
        ]

        button.setStyleSheet(
            "QPushButton {"
            "background-color: rgb(%d,%d,%d);"
            "}" % (
                rgb[0],
                rgb[1],
                rgb[2]
            )
        )

    def _choose_runtime_color(
        self,
        item_id,
        button
    ):
        value = self.toolbox.get_value(
            item_id,
            [0.5, 0.5, 0.5]
        )

        color = _safe_color(
            value
        )

        initial = QtGui.QColor(
            int(color[0] * 255),
            int(color[1] * 255),
            int(color[2] * 255)
        )

        chosen = QtGui.QColorDialog.getColor(
            initial,
            self,
            "Choose Color"
        )

        if not chosen.isValid():
            return

        value = [
            chosen.red() / 255.0,
            chosen.green() / 255.0,
            chosen.blue() / 255.0
        ]

        self.toolbox.store_value(
            item_id,
            value
        )

        self._color_button_style(
            button,
            value
        )

    def _parameter_widget(
        self,
        item,
        compact=False
    ):
        kind = item.get(
            "kind"
        )

        container, layout = self._parameter_container(
            item,
            compact=compact
        )

        if kind == "string":
            control = QtGui.QLineEdit(
                text_type(
                    item.get(
                        "value",
                        ""
                    )
                )
            )

            if compact:
                control.setMinimumWidth(
                    80
                )

            control.editingFinished.connect(
                lambda item_id=item["id"], widget=control:
                self.toolbox.store_value(
                    item_id,
                    text_type(
                        widget.text()
                    )
                )
            )

        elif kind == "integer":
            control = QtGui.QSpinBox()
            control.setRange(
                item["min"],
                item["max"]
            )
            control.setSingleStep(
                item["step"]
            )
            control.setValue(
                item["value"]
            )

            control.valueChanged.connect(
                lambda value, item_id=item["id"]:
                self.toolbox.store_value(
                    item_id,
                    int(value)
                )
            )

        elif kind == "float":
            control = QtGui.QDoubleSpinBox()
            control.setDecimals(
                item["decimals"]
            )
            control.setRange(
                item["min"],
                item["max"]
            )
            control.setSingleStep(
                item["step"]
            )
            control.setValue(
                item["value"]
            )

            control.valueChanged.connect(
                lambda value, item_id=item["id"]:
                self.toolbox.store_value(
                    item_id,
                    float(value)
                )
            )

        elif kind == "menu":
            control = QtGui.QComboBox()
            control.addItems(
                item["items"]
            )

            index = control.findText(
                item["value"]
            )

            if index >= 0:
                control.setCurrentIndex(
                    index
                )

            control.currentIndexChanged.connect(
                lambda index, item_id=item["id"], widget=control:
                self.toolbox.store_value(
                    item_id,
                    text_type(
                        widget.itemText(
                            index
                        )
                    )
                )
            )

        elif kind == "color":
            control = QtGui.QPushButton(                "..."
                if compact
                else "Choose..."
            )

            self._color_button_style(
                control,
                item["value"]
            )

            control.clicked.connect(
                lambda checked=False, item_id=item["id"], widget=control:
                self._choose_runtime_color(
                    item_id,
                    widget
                )
            )

        else:
            return None

        layout.addWidget(
            control,
            1 if kind in (
                "string",
                "menu"
            ) else 0
        )

        return container

    def _row_widget(
        self,
        item
    ):
        row_widget = QtGui.QWidget()
        row_widget.setToolTip(
            self._tooltip(
                item
            )
        )

        layout = QtGui.QHBoxLayout(
            row_widget
        )
        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )
        layout.setSpacing(
            int(
                item.get(
                    "spacing",
                    4
                )
            )
        )

        for child in item.get(
            "items",
            []
        ):
            child_widget = self.build_runtime_widget(
                child,
                compact=True
            )

            if child_widget is not None:
                layout.addWidget(
                    child_widget
                )

        layout.addStretch(
            1
        )

        return row_widget

    def build_runtime_widget(
        self,
        item,
        compact=False
    ):
        kind = item.get(
            "kind"
        )

        if kind == "folder":
            # Normally folders are grouped in _populate_runtime_items().
            # This fallback is useful for direct rendering paths.
            return RuntimeSection(
                self.toolbox,
                item,
                self.content
            )

        if kind == "row":
            return self._row_widget(
                item
            )

        if kind == "button":
            return self._button_widget(
                item
            )

        if kind == "toggle":
            legacy = _toggle_item(
                item
            )
            return self._checkbox_widget(
                legacy,
                compact=compact
            )

        if kind == "checkbox":
            return self._checkbox_widget(
                item,
                compact=compact
            )

        if kind == "field":
            container, layout = self._parameter_container(
                item,
                compact=compact
            )

            control = DisplayField(
                self.toolbox,
                item,
                container
            )

            if compact:
                control.setMinimumWidth(
                    100
                )

            layout.addWidget(
                control,
                1
            )

            self.toolbox.register_field_widget(
                item["id"],
                control
            )

            return container

        if kind == "label":
            label = QtGui.QLabel(
                self._label(
                    item
                )
            )
            label.setToolTip(
                self._tooltip(
                    item
                )
            )
            label.setStyleSheet(
                "color:#bdbdbd; padding:2px 3px;"
            )
            return label

        if kind == "separator":
            line = QtGui.QFrame()

            line.setFrameShape(
                QtGui.QFrame.VLine
                if compact
                else QtGui.QFrame.HLine
            )
            line.setFrameShadow(
                QtGui.QFrame.Sunken
            )

            return line

        if kind in (
            "string",
            "integer",
            "float",
            "menu",
            "color"
        ):
            return self._parameter_widget(
                item,
                compact=compact
            )

        return None

    # ------------------------------------------------------------------
    # Folder behavior
    # ------------------------------------------------------------------

    def toggle(self):
        if self.folder_type != "collapsible":
            return

        self.section["collapsed"] = not bool(
            self.section.get(
                "collapsed",
                False
            )
        )

        self.toolbox.save()
        self.update_state()

    def update_state(self):
        if (
            self.embedded or
            self.folder_type != "collapsible"
        ):
            self.content.setVisible(
                True
            )

            if self.arrow is not None:
                self.arrow.setText(
                    "v"
                )
            return

        collapsed = bool(
            self.section.get(
                "collapsed",
                False
            )
        )

        self.content.setVisible(
            not collapsed
        )

        if self.arrow is not None:
            self.arrow.setText(
                ">" if collapsed else "v"
            )


class RuntimeFolderTabs(QtGui.QFrame):

    def __init__(
        self,
        toolbox,
        folders,
        parent=None
    ):
        QtGui.QFrame.__init__(
            self,
            parent
        )

        layout = QtGui.QVBoxLayout(
            self
        )
        layout.setContentsMargins(
            0,
            0,
            0,
            4
        )
        layout.setSpacing(
            0
        )

        self.tabs = QtGui.QTabWidget()
        layout.addWidget(
            self.tabs
        )

        for folder in folders:
            page = RuntimeSection(
                toolbox,
                folder,
                self.tabs,
                embedded=True
            )

            label = (
                folder.get(
                    "label",
                    folder["name"]
                )
                if folder.get(
                    "show_label",
                    True
                )
                else ""
            )

            self.tabs.addTab(
                page,
                label
            )


class RuntimeFolderRadio(QtGui.QFrame):

    def __init__(
        self,
        toolbox,
        folders,
        parent=None
    ):
        QtGui.QFrame.__init__(
            self,
            parent
        )

        root = QtGui.QVBoxLayout(
            self
        )
        root.setContentsMargins(
            0,
            0,
            0,
            4
        )
        root.setSpacing(
            4
        )

        radio_row = QtGui.QHBoxLayout()
        radio_row.setContentsMargins(
            4,
            2,
            4,
            0
        )
        radio_row.setSpacing(
            8
        )

        self.group = QtGui.QButtonGroup(
            self
        )
        self.stack = QtGui.QStackedWidget()

        for index, folder in enumerate(
            folders
        ):
            label = (
                folder.get(
                    "label",
                    folder["name"]
                )
                if folder.get(
                    "show_label",
                    True
                )
                else ""
            )

            button = QtGui.QRadioButton(
                label
            )

            self.group.addButton(
                button,
                index
            )
            radio_row.addWidget(
                button
            )

            page = RuntimeSection(
                toolbox,
                folder,
                self.stack,
                embedded=True
            )
            self.stack.addWidget(
                page
            )

            button.toggled.connect(
                lambda checked, i=index:
                self._set_page(
                    checked,
                    i
                )
            )

            if index == 0:
                button.setChecked(
                    True
                )

        radio_row.addStretch(
            1
        )

        root.addLayout(
            radio_row
        )
        root.addWidget(
            self.stack
        )

    def _set_page(
        self,
        checked,
        index
    ):
        if checked:
            self.stack.setCurrentIndex(
                index
            )


# ----------------------------------------------------------------------
# Interface tree
# ----------------------------------------------------------------------

class ExistingInterfaceTree(QtGui.QTreeWidget):

    def __init__(
        self,
        editor,
        parent=None
    ):
        QtGui.QTreeWidget.__init__(
            self,
            parent
        )

        self.editor = editor

        self.setHeaderLabels(
            [
                "Existing Interface",
                "Name",
                "Type"
            ]
        )
        self.setColumnWidth(
            0,
            210
        )
        self.setColumnWidth(
            1,
            150
        )
        self.setSelectionMode(
            QtGui.QAbstractItemView.SingleSelection
        )
        self.setDragEnabled(
            True
        )
        self.setAcceptDrops(
            True
        )
        self.setDropIndicatorShown(
            True
        )
        self.setDragDropMode(
            QtGui.QAbstractItemView.InternalMove
        )

    def dropEvent(
        self,
        event
    ):
        current = self.currentItem()

        # Folders, Rows and normal items can be moved through the tree.
        # fix_tree_structure() normalizes invalid destinations afterwards.
        QtGui.QTreeWidget.dropEvent(
            self,
            event
        )

        self.editor.fix_tree_structure()
        self.editor.tree_changed()


# ----------------------------------------------------------------------
# Interface Editor
# ----------------------------------------------------------------------

class InterfaceEditor(QtGui.QDialog):

    PAGE_EMPTY = 0
    PAGE_FOLDER = 1
    PAGE_SECTION = PAGE_FOLDER
    PAGE_BUTTON = 2
    PAGE_STRING = 3
    PAGE_INTEGER = 4
    PAGE_FLOAT = 5
    PAGE_MENU = 6
    PAGE_COLOR = 7
    PAGE_LABEL = 8
    PAGE_SEPARATOR = 9
    PAGE_ROW = 10
    PAGE_FIELD = 11
    PAGE_CHECKBOX = 12


    def __init__(
        self,
        toolbox,
        parent=None
    ):
        QtGui.QDialog.__init__(
            self,
            parent or toolbox
        )

        self.toolbox = toolbox
        self.working = copy.deepcopy(
            toolbox.config
        )

        self.current_kind = None
        self.current_id = None
        self.loading_properties = False

        self.setObjectName(
            EDITOR_OBJECT_NAME
        )
        self.setWindowTitle(
            "Edit Script Toolbox Interface"
        )
        self.resize(
            1220,
            760
        )
        self.setMinimumSize(
            940,
            580
        )
        self.setStyleSheet(
            STYLE
        )

        self.build_ui()
        self.populate_tree()

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def build_ui(self):
        root = QtGui.QVBoxLayout(
            self
        )
        root.setContentsMargins(
            8,
            8,
            8,
            8
        )
        root.setSpacing(7)

        heading = QtGui.QLabel(
            "Edit Parameter Interface  —  Script Toolbox"
        )
        heading.setObjectName(
            "DialogHeading"
        )
        root.addWidget(
            heading
        )

        splitter = QtGui.QSplitter(
            QtCore.Qt.Horizontal
        )
        splitter.setHandleWidth(
            2
        )
        splitter.setChildrenCollapsible(
            False
        )
        root.addWidget(
            splitter,
            1
        )

        # Left ---------------------------------------------------------
        left = QtGui.QWidget()
        left.setObjectName(
            "EditorPane"
        )
        left_layout = QtGui.QVBoxLayout(
            left
        )
        left_layout.setContentsMargins(
            8,
            8,
            8,
            8
        )
        left_layout.setSpacing(
            6
        )

        left_title = QtGui.QLabel(
            "Create Parameters"
        )
        left_title.setObjectName(
            "PaneTitle"
        )
        left_layout.addWidget(
            left_title
        )

        self.palette = QtGui.QListWidget()
        self.palette.setAlternatingRowColors(
            True
        )
        self.palette.setSpacing(
            1
        )

        palette_items = [
            ("Folder", "folder"),
            ("Row", "row"),
            ("Field", "field"),
            ("String", "string"),
            ("Integer", "integer"),
            ("Float", "float"),
            ("Checkbox", "checkbox"),
            ("Menu", "menu"),
            ("Color", "color"),
            ("Button", "button"),
            ("Label", "label"),
            ("Separator", "separator")
        ]

        for label, kind in palette_items:
            item = QtGui.QListWidgetItem(
                label
            )
            item.setData(
                ROLE_KIND,
                kind
            )

            if kind in (
                "folder",
                "row"
            ):
                font = item.font()
                font.setBold(
                    True
                )
                item.setFont(
                    font
                )

            self.palette.addItem(
                item
            )

        self.palette.itemDoubleClicked.connect(
            self.create_from_palette
        )

        left_layout.addWidget(
            self.palette,
            1
        )

        hint = QtGui.QLabel(
            "Double-click to create. Drag items to reorder or nest.\n"
            "Row = horizontal layout. Folder = nested parameter group."
        )
        hint.setObjectName(
            "HintText"
        )
        hint.setWordWrap(
            True
        )
        left_layout.addWidget(
            hint
        )

        splitter.addWidget(
            left
        )

        # Center -------------------------------------------------------
        center = QtGui.QWidget()
        center.setObjectName(
            "EditorPane"
        )
        center_layout = QtGui.QVBoxLayout(
            center
        )
        center_layout.setContentsMargins(
            8,
            8,
            8,
            8
        )
        center_layout.setSpacing(
            6
        )

        toolbar = QtGui.QHBoxLayout()
        toolbar.setSpacing(
            2
        )

        center_title = QtGui.QLabel(
            "Existing Parameters"
        )
        center_title.setObjectName(
            "PaneTitle"
        )
        toolbar.addWidget(
            center_title
        )
        toolbar.addStretch(1)

        up = QtGui.QToolButton()
        up.setObjectName(
            "IconButton"
        )
        up.setIcon(
            _toolbar_icon(
                "up"
            )
        )
        up.setIconSize(
            QtCore.QSize(
                16,
                16
            )
        )
        up.setFixedSize(
            25,
            25
        )
        up.setToolTip(
            "Move Up"
        )
        up.clicked.connect(
            lambda: self.move_selected(
                -1
            )
        )

        down = QtGui.QToolButton()
        down.setObjectName(
            "IconButton"
        )
        down.setIcon(
            _toolbar_icon(
                "down"
            )
        )
        down.setIconSize(
            QtCore.QSize(
                16,
                16
            )
        )
        down.setFixedSize(
            25,
            25
        )
        down.setToolTip(
            "Move Down"
        )
        down.clicked.connect(
            lambda: self.move_selected(
                1
            )
        )

        delete = QtGui.QToolButton()
        delete.setObjectName(
            "IconButton"
        )
        delete.setIcon(
            _toolbar_icon(
                "delete"
            )
        )
        delete.setIconSize(
            QtCore.QSize(
                16,
                16
            )
        )
        delete.setFixedSize(
            25,
            25
        )
        delete.setToolTip(
            "Delete"
        )
        delete.clicked.connect(
            self.delete_selected
        )

        toolbar.addWidget(up)
        toolbar.addWidget(down)
        toolbar.addWidget(delete)

        center_layout.addLayout(
            toolbar
        )

        self.tree = ExistingInterfaceTree(
            self
        )
        self.tree.setAlternatingRowColors(
            True
        )
        self.tree.setUniformRowHeights(
            True
        )
        self.tree.setIndentation(
            18
        )

        self.tree.currentItemChanged.connect(
            self.selection_changed
        )

        center_layout.addWidget(
            self.tree,
            1
        )

        splitter.addWidget(
            center
        )

        # Right --------------------------------------------------------
        right = QtGui.QWidget()
        right.setObjectName(
            "EditorPane"
        )
        right_layout = QtGui.QVBoxLayout(
            right
        )
        right_layout.setContentsMargins(
            8,
            8,
            8,
            8
        )
        right_layout.setSpacing(
            6
        )

        right_title = QtGui.QLabel(
            "Parameter Description"
        )
        right_title.setObjectName(
            "PaneTitle"
        )
        right_layout.addWidget(
            right_title
        )

        self.property_stack = QtGui.QStackedWidget()
        self.property_stack.setObjectName(
            "PropertyStack"
        )
        right_layout.addWidget(
            self.property_stack,
            1
        )

        self.empty_page = QtGui.QLabel(
            "Select a parameter to edit its properties."
        )
        self.empty_page.setObjectName(
            "HintText"
        )
        self.empty_page.setAlignment(
            QtCore.Qt.AlignCenter
        )
        self.property_stack.addWidget(
            self.empty_page
        )

        self.section_page = self.build_section_page()
        self.property_stack.addWidget(
            self.section_page
        )

        self.button_page = self.build_button_page()
        self.property_stack.addWidget(
            self.button_page
        )

        self.string_page = self.build_string_page()
        self.property_stack.addWidget(
            self.string_page
        )

        self.integer_page = self.build_integer_page()
        self.property_stack.addWidget(
            self.integer_page
        )

        self.float_page = self.build_float_page()
        self.property_stack.addWidget(
            self.float_page
        )

        self.menu_page = self.build_menu_page()
        self.property_stack.addWidget(
            self.menu_page
        )

        self.color_page = self.build_color_page()
        self.property_stack.addWidget(
            self.color_page
        )

        self.label_page = self.build_label_page()
        self.property_stack.addWidget(
            self.label_page
        )

        self.separator_page = self.build_separator_page()
        self.property_stack.addWidget(
            self.separator_page
        )

        self.row_page = self.build_row_page()
        self.property_stack.addWidget(
            self.row_page
        )

        self.field_page = self.build_field_page()
        self.property_stack.addWidget(
            self.field_page
        )

        self.checkbox_page = self.build_checkbox_page()
        self.property_stack.addWidget(
            self.checkbox_page
        )

        splitter.addWidget(
            right
        )

        splitter.setSizes(
            [
                220,
                420,
                580
            ]
        )

        # Bottom -------------------------------------------------------
        bottom = QtGui.QHBoxLayout()
        bottom.setSpacing(
            6
        )

        self.status = QtGui.QLabel(
            "Changes are staged until Apply or Accept."
        )
        self.status.setObjectName(
            "EditorStatus"
        )

        import_button = QtGui.QToolButton()
        import_button.setObjectName(
            "IconButton"
        )
        import_button.setIcon(
            _toolbar_icon(
                "import"
            )
        )
        import_button.setIconSize(
            QtCore.QSize(
                16,
                16
            )
        )
        import_button.setFixedSize(
            25,
            25
        )
        import_button.setToolTip(
            "Import Toolbox Settings"
        )
        import_button.clicked.connect(
            self.import_settings
        )

        export_button = QtGui.QToolButton()        export_button.setObjectName(
            "IconButton"
        )
        export_button.setIcon(
            _toolbar_icon(
                "export"
            )
        )
        export_button.setIconSize(
            QtCore.QSize(
                16,
                16
            )
        )
        export_button.setFixedSize(
            25,
            25
        )
        export_button.setToolTip(
            "Export Toolbox Settings"
        )
        export_button.clicked.connect(
            self.export_settings
        )

        bottom.addWidget(
            import_button
        )
        bottom.addWidget(
            export_button
        )
        bottom.addSpacing(
            4
        )
        bottom.addWidget(
            self.status
        )
        bottom.addStretch(1)

        apply_button = QtGui.QPushButton(
            "Apply"
        )
        apply_button.setMinimumWidth(
            78
        )
        apply_button.clicked.connect(
            self.apply_changes
        )

        accept_button = QtGui.QPushButton(
            "Accept"
        )
        accept_button.setObjectName(
            "AcceptButton"
        )
        accept_button.setMinimumWidth(
            78
        )
        accept_button.clicked.connect(
            self.accept_changes
        )

        cancel_button = QtGui.QPushButton(
            "Cancel"
        )
        cancel_button.setMinimumWidth(
            78
        )
        cancel_button.clicked.connect(
            self.reject
        )

        bottom.addWidget(
            apply_button
        )
        bottom.addWidget(
            accept_button
        )
        bottom.addWidget(
            cancel_button
        )

        root.addLayout(
            bottom
        )

    # ------------------------------------------------------------------
    # Property pages
    # ------------------------------------------------------------------

    def add_identity_rows(
        self,
        form,
        default_label_text="Label"
    ):
        internal_name = QtGui.QLineEdit()
        label = QtGui.QLineEdit()
        show_label = QtGui.QCheckBox(
            "Show Label"
        )
        show_label.setChecked(
            True
        )

        internal_name.setToolTip(
            "Internal script name. Use letters, numbers and underscores."
        )
        label.setToolTip(
            "Visible label shown in the Toolbox interface."
        )
        show_label.setToolTip(
            "Disable to hide the visible Label in the runtime interface."
        )

        form.addRow(
            "Name",
            internal_name
        )
        form.addRow(
            default_label_text,
            label
        )
        form.addRow(
            "",
            show_label
        )

        return (
            internal_name,
            label,
            show_label
        )

    def build_section_page(self):
        # Method name retained for compatibility; UI item is now Folder.
        page = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(
            page
        )
        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        form = QtGui.QFormLayout()
        form.setHorizontalSpacing(
            8
        )
        form.setVerticalSpacing(
            6
        )
        form.setLabelAlignment(
            QtCore.Qt.AlignLeft |
            QtCore.Qt.AlignVCenter
        )

        (
            self.section_internal_name,
            self.section_label,
            self.section_show_label
        ) = self.add_identity_rows(
            form,
            "Label"
        )

        self.section_folder_type = QtGui.QComboBox()
        self.section_folder_type.addItems([
            "Collapsible",
            "Simple",
            "Tabs",
            "Radio Buttons"
        ])

        self.section_collapsed = QtGui.QCheckBox(
            "Collapsed by default"
        )

        form.addRow(
            "Folder Type",
            self.section_folder_type
        )
        form.addRow(
            "",
            self.section_collapsed
        )

        layout.addLayout(
            form
        )

        note = QtGui.QLabel(
            "Tabs and Radio Buttons automatically group consecutive "
            "Folders of the same type."
        )
        note.setWordWrap(
            True
        )
        note.setStyleSheet(
            "color:#888888;"
        )

        layout.addWidget(
            note
        )
        layout.addStretch(
            1
        )

        self.section_internal_name.textEdited.connect(
            self.property_edited
        )
        self.section_label.textEdited.connect(
            self.property_edited
        )
        self.section_show_label.toggled.connect(
            self.property_edited
        )
        self.section_folder_type.currentIndexChanged.connect(
            self.folder_type_changed
        )
        self.section_collapsed.toggled.connect(
            self.property_edited
        )

        return page

    def folder_type_changed(
        self,
        *args
    ):
        is_collapsible = (
            self.section_folder_type.currentIndex() == 0
        )

        self.section_collapsed.setEnabled(
            is_collapsible
        )

        if not self.loading_properties:
            self.property_edited()


    def build_button_page(self):
        page = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # --------------------------------------------------------------
        # Parameter properties
        # --------------------------------------------------------------
        form = QtGui.QFormLayout()
        form.setHorizontalSpacing(
            8
        )
        form.setVerticalSpacing(
            6
        )
        form.setLabelAlignment(
            QtCore.Qt.AlignLeft |
            QtCore.Qt.AlignVCenter
        )

        (
            self.button_internal_name,
            self.button_label,
            self.button_show_label
        ) = self.add_identity_rows(
            form,
            "Label"
        )

        self.button_language = QtGui.QComboBox()
        self.button_language.addItems(
            ["Python", "MEL"]
        )

        self.button_tooltip = QtGui.QLineEdit()
        self.button_color = QtGui.QPushButton(
            "Choose..."
        )

        form.addRow(
            "Language",
            self.button_language
        )
        form.addRow(
            "Tooltip",
            self.button_tooltip
        )
        form.addRow(
            "Color",
            self.button_color
        )

        layout.addLayout(form)

        # --------------------------------------------------------------
        # Houdini-like code toolbar
        # --------------------------------------------------------------
        toolbar = QtGui.QHBoxLayout()
        toolbar.setSpacing(
            2
        )

        def add_tool_button(icon_kind, tooltip, callback):
            button = QtGui.QToolButton()
            button.setIcon(
                _toolbar_icon(icon_kind)
            )
            button.setIconSize(
                QtCore.QSize(18, 18)
            )
            button.setFixedSize(
                26,
                26
            )
            button.setToolTip(tooltip)
            button.clicked.connect(callback)
            toolbar.addWidget(button)
            return button

        add_tool_button(
            "undo",
            "Undo",
            self.code_undo
        )
        add_tool_button(
            "redo",
            "Redo",
            self.code_redo
        )

        toolbar.addSpacing(4)

        add_tool_button(
            "cut",
            "Cut",
            self.code_cut
        )
        add_tool_button(
            "copy",
            "Copy",
            self.code_copy
        )
        add_tool_button(
            "paste",
            "Paste",
            self.code_paste
        )

        toolbar.addSpacing(4)

        add_tool_button(
            "find",
            "Find text",
            self.code_find
        )
        add_tool_button(
            "find_next",
            "Find next",
            self.code_find_next
        )

        toolbar.addSpacing(4)

        add_tool_button(
            "comment",
            "Comment selected/current lines",
            self.code_comment
        )
        add_tool_button(
            "uncomment",
            "Uncomment selected/current lines",
            self.code_uncomment
        )
        add_tool_button(
            "indent",
            "Indent selected/current lines",
            self.code_indent
        )
        add_tool_button(
            "unindent",
            "Unindent selected/current lines",
            self.code_unindent
        )

        toolbar.addSpacing(4)

        self.code_run_button = add_tool_button(
            "run",
            "Run current script",
            self.code_run
        )

        toolbar.addStretch(1)

        layout.addLayout(toolbar)

        # --------------------------------------------------------------
        # Click / Shift+Click tabs + Output
        # --------------------------------------------------------------
        self.code_splitter = QtGui.QSplitter(
            QtCore.Qt.Vertical
        )

        self.code_tabs = QtGui.QTabWidget()

        self.click_editor = CodeEditor()
        self.shift_editor = CodeEditor()

        self.code_tabs.addTab(
            self.click_editor,
            "Click Script"
        )
        self.code_tabs.addTab(
            self.shift_editor,
            "Shift + Click"
        )

        self.code_splitter.addWidget(
            self.code_tabs
        )

        self.code_output = QtGui.QPlainTextEdit()
        self.code_output.setReadOnly(True)
        self.code_output.setLineWrapMode(
            QtGui.QPlainTextEdit.NoWrap
        )

        output_font = QtGui.QFont(
            "Consolas"
        )
        output_font.setStyleHint(
            QtGui.QFont.Monospace
        )
        output_font.setPointSize(9)
        self.code_output.setFont(
            output_font
        )

        self.code_splitter.addWidget(
            self.code_output
        )

        self.code_splitter.setSizes(
            [420, 115]
        )

        layout.addWidget(
            self.code_splitter,
            1
        )

        # --------------------------------------------------------------
        # Editor status
        # --------------------------------------------------------------
        status_row = QtGui.QHBoxLayout()

        self.code_status_label = QtGui.QLabel(
            "Ready"
        )

        self.code_cursor_label = QtGui.QLabel(
            "Ln 1, Col 1"
        )

        clear_output = QtGui.QToolButton()
        clear_output.setIcon(
            _toolbar_icon("clear")
        )
        clear_output.setIconSize(
            QtCore.QSize(18, 18)
        )
        clear_output.setFixedSize(
            26,
            26
        )
        clear_output.setToolTip(
            "Clear Output"
        )
        clear_output.clicked.connect(
            self.code_output.clear
        )

        status_row.addWidget(
            clear_output
        )
        status_row.addWidget(
            self.code_status_label
        )
        status_row.addStretch(1)
        status_row.addWidget(
            self.code_cursor_label
        )

        layout.addLayout(
            status_row
        )

        hint = QtGui.QLabel(
            "Python namespace: cmds, mel, toolbox. "
            "Run executes the currently visible Click/Shift script."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet(
            "color:#888888;"
        )

        layout.addWidget(
            hint
        )

        # --------------------------------------------------------------
        # Highlighters / signals
        # --------------------------------------------------------------
        self.click_highlighter = ScriptHighlighter(
            self.click_editor.document(),
            "python"
        )

        self.shift_highlighter = ScriptHighlighter(
            self.shift_editor.document(),
            "python"
        )

        self.current_button_color = [
            0.25,
            0.25,
            0.25
        ]

        self._last_code_find = ""

        self.button_internal_name.textEdited.connect(
            self.property_edited
        )
        self.button_label.textEdited.connect(
            self.property_edited
        )
        self.button_show_label.toggled.connect(
            self.property_edited
        )
        self.button_tooltip.textEdited.connect(
            self.property_edited
        )
        self.button_language.currentIndexChanged.connect(
            self.language_changed
        )
        self.button_color.clicked.connect(
            self.choose_button_color
        )

        self.click_editor.textChanged.connect(
            self.property_edited
        )
        self.shift_editor.textChanged.connect(
            self.property_edited
        )

        self.click_editor.cursorPositionChanged.connect(
            self.code_update_cursor_position
        )
        self.shift_editor.cursorPositionChanged.connect(
            self.code_update_cursor_position
        )

        self.code_tabs.currentChanged.connect(
            self.code_update_cursor_position
        )

        return page

    def build_string_page(self):
        page = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        form = QtGui.QFormLayout()
        form.setHorizontalSpacing(
            8
        )
        form.setVerticalSpacing(
            6
        )
        form.setLabelAlignment(
            QtCore.Qt.AlignLeft |
            QtCore.Qt.AlignVCenter
        )

        (
            self.string_internal_name,
            self.string_label,
            self.string_show_label
        ) = self.add_identity_rows(
            form,
            "Label"
        )

        self.string_value = QtGui.QLineEdit()
        self.string_tooltip = QtGui.QLineEdit()

        form.addRow(
            "Value",
            self.string_value
        )
        form.addRow(
            "Tooltip",
            self.string_tooltip
        )

        layout.addLayout(form)
        layout.addStretch(1)

        self.string_internal_name.textEdited.connect(
            self.property_edited
        )
        self.string_label.textEdited.connect(
            self.property_edited
        )
        self.string_show_label.toggled.connect(
            self.property_edited
        )
        self.string_value.textEdited.connect(
            self.property_edited
        )
        self.string_tooltip.textEdited.connect(
            self.property_edited
        )

        return page

    def build_integer_page(self):
        page = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        form = QtGui.QFormLayout()
        form.setHorizontalSpacing(
            8
        )
        form.setVerticalSpacing(
            6
        )
        form.setLabelAlignment(
            QtCore.Qt.AlignLeft |
            QtCore.Qt.AlignVCenter
        )

        (
            self.integer_internal_name,
            self.integer_label,
            self.integer_show_label
        ) = self.add_identity_rows(
            form,
            "Label"
        )

        self.integer_value = QtGui.QSpinBox()
        self.integer_min = QtGui.QSpinBox()
        self.integer_max = QtGui.QSpinBox()
        self.integer_step = QtGui.QSpinBox()
        self.integer_tooltip = QtGui.QLineEdit()

        for spin in (
            self.integer_value,
            self.integer_min,
            self.integer_max
        ):
            spin.setRange(
                -1000000000,
                1000000000
            )

        self.integer_step.setRange(
            1,
            1000000000
        )

        form.addRow("Value", self.integer_value)
        form.addRow("Minimum", self.integer_min)
        form.addRow("Maximum", self.integer_max)
        form.addRow("Step", self.integer_step)
        form.addRow("Tooltip", self.integer_tooltip)

        layout.addLayout(form)
        layout.addStretch(1)

        self.integer_internal_name.textEdited.connect(
            self.property_edited
        )
        self.integer_label.textEdited.connect(
            self.property_edited
        )
        self.integer_show_label.toggled.connect(
            self.property_edited
        )
        self.integer_value.valueChanged.connect(
            self.property_edited
        )
        self.integer_min.valueChanged.connect(
            self.property_edited
        )
        self.integer_max.valueChanged.connect(
            self.property_edited
        )
        self.integer_step.valueChanged.connect(
            self.property_edited
        )
        self.integer_tooltip.textEdited.connect(
            self.property_edited
        )

        return page

    def build_float_page(self):
        page = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        form = QtGui.QFormLayout()
        form.setHorizontalSpacing(
            8
        )
        form.setVerticalSpacing(
            6
        )
        form.setLabelAlignment(
            QtCore.Qt.AlignLeft |
            QtCore.Qt.AlignVCenter
        )

        (
            self.float_internal_name,
            self.float_label,
            self.float_show_label
        ) = self.add_identity_rows(
            form,
            "Label"
        )

        self.float_value = QtGui.QDoubleSpinBox()
        self.float_min = QtGui.QDoubleSpinBox()
        self.float_max = QtGui.QDoubleSpinBox()
        self.float_step = QtGui.QDoubleSpinBox()
        self.float_decimals = QtGui.QSpinBox()
        self.float_tooltip = QtGui.QLineEdit()

        for spin in (
            self.float_value,
            self.float_min,
            self.float_max
        ):
            spin.setRange(
                -1000000000.0,
                1000000000.0
            )
            spin.setDecimals(6)

        self.float_step.setRange(
            0.000001,
            1000000000.0
        )
        self.float_step.setDecimals(6)
        self.float_decimals.setRange(0, 8)

        form.addRow("Value", self.float_value)
        form.addRow("Minimum", self.float_min)
        form.addRow("Maximum", self.float_max)
        form.addRow("Step", self.float_step)
        form.addRow("Decimals", self.float_decimals)
        form.addRow("Tooltip", self.float_tooltip)

        layout.addLayout(form)
        layout.addStretch(1)

        self.float_internal_name.textEdited.connect(
            self.property_edited
        )
        self.float_label.textEdited.connect(
            self.property_edited
        )
        self.float_show_label.toggled.connect(
            self.property_edited
        )
        self.float_value.valueChanged.connect(
            self.property_edited
        )
        self.float_min.valueChanged.connect(
            self.property_edited
        )
        self.float_max.valueChanged.connect(
            self.property_edited
        )
        self.float_step.valueChanged.connect(
            self.property_edited
        )
        self.float_decimals.valueChanged.connect(
            self.property_edited
        )
        self.float_tooltip.textEdited.connect(
            self.property_edited
        )

        return page

    def build_toggle_page(self):
        page = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        form = QtGui.QFormLayout()
        form.setHorizontalSpacing(
            8
        )
        form.setVerticalSpacing(
            6
        )
        form.setLabelAlignment(
            QtCore.Qt.AlignLeft |
            QtCore.Qt.AlignVCenter
        )

        (
            self.toggle_internal_name,
            self.toggle_label,
            self.toggle_show_label
        ) = self.add_identity_rows(
            form,
            "Label"
        )

        self.toggle_value = QtGui.QCheckBox(
            "Enabled"
        )
        self.toggle_tooltip = QtGui.QLineEdit()

        form.addRow("Value", self.toggle_value)
        form.addRow("Tooltip", self.toggle_tooltip)

        layout.addLayout(form)
        layout.addStretch(1)

        self.toggle_internal_name.textEdited.connect(
            self.property_edited
        )
        self.toggle_label.textEdited.connect(
            self.property_edited
        )
        self.toggle_show_label.toggled.connect(
            self.property_edited
        )
        self.toggle_value.toggled.connect(
            self.property_edited
        )
        self.toggle_tooltip.textEdited.connect(
            self.property_edited
        )

        return page

    def build_checkbox_page(self):
        page = QtGui.QWidget()

        layout = QtGui.QVBoxLayout(
            page
        )
        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        form = QtGui.QFormLayout()
        form.setHorizontalSpacing(
            8
        )
        form.setVerticalSpacing(
            6
        )
        form.setLabelAlignment(
            QtCore.Qt.AlignLeft |
            QtCore.Qt.AlignVCenter
        )

        (
            self.checkbox_internal_name,
            self.checkbox_label,
            self.checkbox_show_label
        ) = self.add_identity_rows(
            form,
            "Label"
        )

        self.checkbox_label_position = QtGui.QComboBox()
        self.checkbox_label_position.addItems([
            "Right",
            "Left"
        ])

        self.checkbox_value = QtGui.QCheckBox(
            "Checked"
        )
        self.checkbox_tooltip = QtGui.QLineEdit()

        form.addRow(
            "Label Position",
            self.checkbox_label_position
        )
        form.addRow(
            "Value",
            self.checkbox_value
        )
        form.addRow(
            "Tooltip",
            self.checkbox_tooltip
        )

        layout.addLayout(
            form
        )

        note = QtGui.QLabel(
            "One Checkbox item replaces the old Toggle/Checkbox pair. "
            "Use Label Position to choose Houdini-style left or right layout."
        )
        note.setWordWrap(
            True
        )
        note.setStyleSheet(
            "color:#888888;"
        )

        layout.addWidget(
            note
        )
        layout.addStretch(
            1
        )

        self.checkbox_internal_name.textEdited.connect(
            self.property_edited
        )
        self.checkbox_label.textEdited.connect(
            self.property_edited
        )
        self.checkbox_show_label.toggled.connect(
            self.property_edited
        )
        self.checkbox_label_position.currentIndexChanged.connect(
            self.property_edited
        )
        self.checkbox_value.toggled.connect(
            self.property_edited
        )
        self.checkbox_tooltip.textEdited.connect(
            self.property_edited
        )

        return page


    def build_menu_page(self):
        page = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        form = QtGui.QFormLayout()
        form.setHorizontalSpacing(
            8
        )
        form.setVerticalSpacing(
            6
        )
        form.setLabelAlignment(
            QtCore.Qt.AlignLeft |
            QtCore.Qt.AlignVCenter
        )

        (
            self.menu_internal_name,
            self.menu_label,
            self.menu_show_label
        ) = self.add_identity_rows(
            form,
            "Label"
        )

        self.menu_tooltip = QtGui.QLineEdit()

        form.addRow(
            "Tooltip",
            self.menu_tooltip
        )

        layout.addLayout(form)
        layout.addWidget(
            QtGui.QLabel(
                "Menu Items (one per line)"
            )
        )

        self.menu_items = QtGui.QPlainTextEdit()
        self.menu_items.setMaximumHeight(150)
        layout.addWidget(self.menu_items)

        current_row = QtGui.QHBoxLayout()
        current_row.addWidget(
            QtGui.QLabel(
                "Current Value"
            )
        )

        self.menu_value = QtGui.QComboBox()
        current_row.addWidget(
            self.menu_value,
            1
        )

        layout.addLayout(current_row)
        layout.addStretch(1)

        self.menu_internal_name.textEdited.connect(
            self.property_edited
        )
        self.menu_label.textEdited.connect(
            self.property_edited
        )
        self.menu_show_label.toggled.connect(
            self.property_edited
        )
        self.menu_tooltip.textEdited.connect(
            self.property_edited
        )
        self.menu_items.textChanged.connect(
            self.menu_items_edited
        )
        self.menu_value.currentIndexChanged.connect(
            self.property_edited
        )

        return page

    def build_color_page(self):
        page = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        form = QtGui.QFormLayout()
        form.setHorizontalSpacing(
            8
        )
        form.setVerticalSpacing(
            6
        )
        form.setLabelAlignment(
            QtCore.Qt.AlignLeft |
            QtCore.Qt.AlignVCenter
        )

        (
            self.color_internal_name,
            self.color_label,
            self.color_show_label
        ) = self.add_identity_rows(
            form,
            "Label"
        )

        self.color_value = QtGui.QPushButton(
            "Choose..."
        )
        self.color_tooltip = QtGui.QLineEdit()

        form.addRow("Value", self.color_value)
        form.addRow("Tooltip", self.color_tooltip)

        layout.addLayout(form)
        layout.addStretch(1)

        self.current_param_color = [
            0.5,
            0.5,
            0.5
        ]

        self.color_internal_name.textEdited.connect(
            self.property_edited
        )
        self.color_label.textEdited.connect(
            self.property_edited
        )
        self.color_show_label.toggled.connect(
            self.property_edited
        )
        self.color_value.clicked.connect(
            self.choose_param_color
        )
        self.color_tooltip.textEdited.connect(
            self.property_edited
        )

        return page

    def build_label_page(self):
        page = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        form = QtGui.QFormLayout()
        form.setHorizontalSpacing(
            8
        )
        form.setVerticalSpacing(
            6
        )
        form.setLabelAlignment(
            QtCore.Qt.AlignLeft |
            QtCore.Qt.AlignVCenter
        )

        (
            self.label_internal_name,
            self.label_label,
            self.label_show_label
        ) = self.add_identity_rows(
            form,
            "Label"
        )

        self.label_tooltip = QtGui.QLineEdit()

        form.addRow(
            "Tooltip",
            self.label_tooltip
        )

        layout.addLayout(form)
        layout.addStretch(1)

        self.label_internal_name.textEdited.connect(
            self.property_edited
        )
        self.label_label.textEdited.connect(
            self.property_edited
        )
        self.label_show_label.toggled.connect(
            self.property_edited
        )
        self.label_tooltip.textEdited.connect(
            self.property_edited
        )

        return page

    def build_separator_page(self):
        page = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        form = QtGui.QFormLayout()
        form.setHorizontalSpacing(
            8
        )
        form.setVerticalSpacing(
            6
        )
        form.setLabelAlignment(
            QtCore.Qt.AlignLeft |
            QtCore.Qt.AlignVCenter
        )

        (
            self.separator_internal_name,
            self.separator_label,
            self.separator_show_label
        ) = self.add_identity_rows(
            form,
            "Label"
        )

        layout.addLayout(form)

        note = QtGui.QLabel(
            "Separator Label is only used in the interface editor; "
            "the runtime separator is a line."
        )
        note.setWordWrap(True)
        note.setStyleSheet(
            "color:#888888;"
        )

        layout.addWidget(note)
        layout.addStretch(1)

        self.separator_internal_name.textEdited.connect(
            self.property_edited
        )
        self.separator_label.textEdited.connect(
            self.property_edited
        )
        self.separator_show_label.toggled.connect(
            self.property_edited
        )

        return page

    def build_field_page(self):
        page = QtGui.QWidget()

        layout = QtGui.QVBoxLayout(
            page
        )
        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        form = QtGui.QFormLayout()
        form.setHorizontalSpacing(
            8
        )
        form.setVerticalSpacing(
            6
        )
        form.setLabelAlignment(
            QtCore.Qt.AlignLeft |
            QtCore.Qt.AlignVCenter
        )

        (
            self.field_internal_name,
            self.field_label,
            self.field_show_label
        ) = self.add_identity_rows(
            form,
            "Label"
        )

        self.field_source = QtGui.QComboBox()
        self.field_source.addItems([
            "Value / Script Result",
            "Maya Selection"
        ])

        self.field_value = QtGui.QLineEdit()
        self.field_placeholder = QtGui.QLineEdit()

        self.field_selectable = QtGui.QCheckBox(
            "Selectable text"
        )

        self.field_select_scene = QtGui.QCheckBox(
            "Select Maya objects on double-click"
        )

        self.field_multiple = QtGui.QCheckBox(
            "Allow multiple selected objects"
        )

        self.field_long_names = QtGui.QCheckBox(
            "Use full DAG paths"
        )

        self.field_tooltip = QtGui.QLineEdit()

        form.addRow(
            "Source",
            self.field_source
        )
        form.addRow(
            "Value",
            self.field_value
        )
        form.addRow(
            "Placeholder",
            self.field_placeholder
        )
        form.addRow(
            "",
            self.field_selectable
        )
        form.addRow(
            "",
            self.field_select_scene
        )
        form.addRow(
            "",
            self.field_multiple
        )
        form.addRow(
            "",
            self.field_long_names
        )
        form.addRow(
            "Tooltip",
            self.field_tooltip
        )

        layout.addLayout(
            form
        )

        note = QtGui.QLabel(
            "For button/script results use:\\n"
            'toolbox.set_result("field_name", value)\\n\\n'
            "Maya Selection source updates automatically."
        )
        note.setWordWrap(
            True
        )
        note.setStyleSheet(
            "color:#888888;"
        )

        layout.addWidget(
            note
        )
        layout.addStretch(
            1
        )

        self.field_internal_name.textEdited.connect(
            self.property_edited
        )
        self.field_label.textEdited.connect(
            self.property_edited
        )
        self.field_show_label.toggled.connect(
            self.property_edited
        )
        self.field_source.currentIndexChanged.connect(
            self.field_source_changed
        )
        self.field_value.textEdited.connect(
            self.property_edited
        )
        self.field_placeholder.textEdited.connect(
            self.property_edited
        )
        self.field_selectable.toggled.connect(
            self.property_edited
        )
        self.field_select_scene.toggled.connect(
            self.property_edited
        )
        self.field_multiple.toggled.connect(
            self.property_edited
        )
        self.field_long_names.toggled.connect(
            self.property_edited
        )
        self.field_tooltip.textEdited.connect(
            self.property_edited
        )

        return page

    def field_source_changed(
        self,
        *args
    ):
        is_selection = (
            self.field_source.currentIndex() == 1
        )

        self.field_value.setEnabled(
            not is_selection
        )

        self.field_multiple.setEnabled(
            is_selection
        )

        self.field_long_names.setEnabled(
            is_selection
        )

        if not self.loading_properties:
            self.property_edited()


    def build_row_page(self):
        page = QtGui.QWidget()

        layout = QtGui.QVBoxLayout(
            page
        )
        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        form = QtGui.QFormLayout()
        form.setHorizontalSpacing(
            8
        )
        form.setVerticalSpacing(
            6
        )
        form.setLabelAlignment(
            QtCore.Qt.AlignLeft |
            QtCore.Qt.AlignVCenter
        )

        (
            self.row_internal_name,
            self.row_label,
            self.row_show_label
        ) = self.add_identity_rows(
            form,
            "Label"
        )

        self.row_spacing = QtGui.QSpinBox()
        self.row_spacing.setRange(
            0,
            30
        )

        form.addRow(
            "Spacing",
            self.row_spacing
        )

        layout.addLayout(
            form
        )

        note = QtGui.QLabel(
            "Row is a technical horizontal container. "
            "Its Label is shown only in the Interface Editor."
        )
        note.setWordWrap(
            True
        )
        note.setStyleSheet(
            "color:#888888;"
        )

        layout.addWidget(
            note
        )
        layout.addStretch(
            1
        )

        self.row_internal_name.textEdited.connect(
            self.property_edited
        )
        self.row_label.textEdited.connect(
            self.property_edited
        )
        self.row_show_label.toggled.connect(
            self.property_edited
        )
        self.row_spacing.valueChanged.connect(
            self.property_edited
        )

        return page


    # ------------------------------------------------------------------
    # Tree helpers
    # ------------------------------------------------------------------

    def set_item_data(
        self,
        tree_item,
        kind,
        item_id
    ):
        tree_item.setData(
            0,
            ROLE_KIND,
            kind
        )
        tree_item.setData(
            0,
            ROLE_ID,
            item_id
        )

    def item_data(
        self,
        tree_item,
        role
    ):
        value = tree_item.data(
            0,
            role
        )

        try:
            value = value.toString()
        except Exception:
            pass

        return text_type(
            value
        )

    def tree_item_by_id(
        self,
        item_id
    ):
        if not item_id:
            return None

        def recurse(tree_item):
            if self.item_data(
                tree_item,
                ROLE_ID
            ) == item_id:
                return tree_item

            for index in range(
                tree_item.childCount()
            ):
                found = recurse(
                    tree_item.child(
                        index
                    )
                )

                if found is not None:
                    return found

            return None

        for section_index in range(
            self.tree.topLevelItemCount()
        ):
            found = recurse(
                self.tree.topLevelItem(
                    section_index
                )
            )

            if found is not None:
                return found

        return None

    def populate_tree(self):
        self.tree.blockSignals(
            True
        )
        self.tree.clear()

        def make_child(
            item
        ):
            kind = item.get(
                "kind",
                "button"
            )

            child = QtGui.QTreeWidgetItem(
                [
                    item.get(
                        "label",
                        item["name"]
                    ),
                    item["name"],
                    kind.title()
                ]
            )

            self.set_item_data(
                child,
                kind,
                item["id"]
            )

            flags = child.flags()
            flags |= QtCore.Qt.ItemIsDragEnabled

            if kind in (
                "row",
                "folder"
            ):
                flags |= QtCore.Qt.ItemIsDropEnabled
            else:
                flags &= ~QtCore.Qt.ItemIsDropEnabled

            child.setFlags(
                flags
            )

            if kind in (
                "row",
                "folder"
            ):
                for nested_item in item.get(
                    "items",
                    []
                ):
                    child.addChild(
                        make_child(
                            nested_item
                        )
                    )

                child.setExpanded(
                    True
                )

            return child

        for section in self.working["sections"]:
            section_item = QtGui.QTreeWidgetItem(
                [
                    section.get(
                        "label",
                        section["name"]
                    ),
                    section["name"],
                    "Folder"
                ]
            )

            self.set_item_data(
                section_item,
                "folder",
                section["id"]
            )

            flags = section_item.flags()
            flags |= QtCore.Qt.ItemIsDragEnabled
            flags |= QtCore.Qt.ItemIsDropEnabled
            section_item.setFlags(
                flags
            )

            self.tree.addTopLevelItem(
                section_item
            )

            for item in section["items"]:
                section_item.addChild(
                    make_child(
                        item
                    )
                )

            section_item.setExpanded(
                True
            )

        self.tree.blockSignals(
            False
        )

        if self.tree.topLevelItemCount():
            self.tree.setCurrentItem(
                self.tree.topLevelItem(
                    0
                )
            )

    def fix_tree_structure(self):
        """
        Valid structure:

            Folder
                normal item
                Row
                    normal item
                Folder
                    ...
                    Folder
                        ...

        Rules:
        - Root contains only Folders.
        - Folder can contain normal items, Rows and other Folders.
        - Row can contain only normal items.
        - Folder nesting depth is unlimited.
        """

        def make_default_root_folder():
            section_data = _section({
                "name": "my_tools",
                "label": "My Tools"
            })

            folder = QtGui.QTreeWidgetItem(
                [
                    section_data["label"],
                    section_data["name"],
                    "Folder"
                ]
            )

            self.set_item_data(
                folder,
                "folder",
                section_data["id"]
            )

            flags = folder.flags()
            flags |= QtCore.Qt.ItemIsDragEnabled
            flags |= QtCore.Qt.ItemIsDropEnabled
            folder.setFlags(
                flags
            )

            folder.setExpanded(
                True
            )

            return folder

        # --------------------------------------------------------------
        # Root may contain only Folders.
        # --------------------------------------------------------------
        index = 0

        while index < self.tree.topLevelItemCount():
            item = self.tree.topLevelItem(
                index
            )

            if self.item_data(
                item,
                ROLE_KIND
            ) == "folder":
                index += 1
                continue

            orphan = self.tree.takeTopLevelItem(
                index
            )

            target = None

            if index > 0:
                candidate = self.tree.topLevelItem(
                    index - 1
                )

                if (
                    candidate is not None and
                    self.item_data(
                        candidate,
                        ROLE_KIND
                    ) == "folder"
                ):
                    target = candidate

            if (
                target is None and
                self.tree.topLevelItemCount()
            ):
                target = self.tree.topLevelItem(
                    0
                )

            if target is None:
                target = make_default_root_folder()
                self.tree.addTopLevelItem(
                    target
                )

            target.addChild(
                orphan
            )
            target.setExpanded(
                True
            )

        # --------------------------------------------------------------
        # Recursively normalize Folder / Row children.
        # --------------------------------------------------------------
        def normalize_folder(
            folder_item
        ):
            child_index = 0

            while child_index < folder_item.childCount():
                child = folder_item.child(
                    child_index
                )

                kind = self.item_data(
                    child,
                    ROLE_KIND
                )

                if kind == "folder":
                    normalize_folder(
                        child
                    )
                    child.setExpanded(
                        True
                    )
                    child_index += 1
                    continue

                if kind == "row":
                    row_index = 0

                    while row_index < child.childCount():
                        nested = child.child(
                            row_index
                        )

                        nested_kind = self.item_data(
                            nested,
                            ROLE_KIND
                        )

                        if nested_kind in (
                            "row",
                            "folder"
                        ):
                            nested = child.takeChild(
                                row_index
                            )

                            folder_item.insertChild(
                                child_index + 1,
                                nested
                            )

                            # The inserted item is now a sibling of the Row.
                            # Do not increment row_index because takeChild()
                            # shifted the remaining row children.
                            child_index += 1
                            continue

                        row_index += 1

                    child.setExpanded(
                        True
                    )
                    child_index += 1
                    continue

                # Normal controls cannot contain children.
                while child.childCount():
                    nested = child.takeChild(
                        0
                    )

                    folder_item.insertChild(
                        child_index + 1,
                        nested
                    )
                    child_index += 1

                child_index += 1

            folder_item.setExpanded(
                True
            )

        for root_index in range(
            self.tree.topLevelItemCount()
        ):
            root_folder = self.tree.topLevelItem(
                root_index
            )

            normalize_folder(
                root_folder
            )

    # ------------------------------------------------------------------
    # Working model
    # ------------------------------------------------------------------

    def find_data(
        self,
        item_id
    ):
        def recurse(
            items
        ):
            for item in items:
                if item["id"] == item_id:
                    return item

                if item.get(
                    "kind"
                ) in (
                    "row",
                    "folder"
                ):
                    found = recurse(
                        item.get(
                            "items",
                            []
                        )
                    )

                    if found is not None:
                        return found

            return None

        for section in self.working["sections"]:
            if section["id"] == item_id:
                return section

            found = recurse(
                section["items"]
            )

            if found is not None:
                return found

        return None

    def sync_working_from_tree(self):
        self.flush_current_properties()

        existing = {}

        def collect(
            items
        ):
            for item in items:
                existing[
                    item["id"]
                ] = item

                if item.get(
                    "kind"
                ) in (
                    "row",
                    "folder"
                ):
                    collect(
                        item.get(
                            "items",
                            []
                        )
                    )

        for section in self.working["sections"]:
            existing[
                section["id"]
            ] = section
            collect(
                section["items"]
            )

        def item_from_tree(
            tree_item
        ):
            item_id = self.item_data(
                tree_item,
                ROLE_ID
            )
            kind = self.item_data(
                tree_item,
                ROLE_KIND
            )

            item = existing.get(
                item_id
            )

            if item is None:
                if kind == "folder":
                    item = _folder_item({
                        "id": item_id,
                        "name": text_type(
                            tree_item.text(
                                1
                            )
                        ),
                        "label": text_type(
                            tree_item.text(
                                0
                            )
                        )
                    })
                else:
                    item = _new_item_by_kind(
                        kind,
                        {
                            "id": item_id,
                            "name": text_type(
                                tree_item.text(
                                    1
                                )
                            ),
                            "label": text_type(                                tree_item.text(
                                    0
                                )
                            )
                        }
                    )

            item["label"] = text_type(
                tree_item.text(
                    0
                )
            )
            item["name"] = _sanitize_internal_name(
                text_type(
                    tree_item.text(
                        1
                    )
                ),
                kind
            )

            if kind == "row":
                row_items = []

                for child_index in range(
                    tree_item.childCount()
                ):
                    child = tree_item.child(
                        child_index
                    )

                    child_kind = self.item_data(
                        child,
                        ROLE_KIND
                    )

                    if child_kind in (
                        "folder",
                        "row"
                    ):
                        continue

                    row_items.append(
                        item_from_tree(
                            child
                        )
                    )

                item["items"] = row_items

            elif kind == "folder":
                folder_items = []

                for child_index in range(
                    tree_item.childCount()
                ):
                    child = tree_item.child(
                        child_index
                    )

                    folder_items.append(
                        item_from_tree(
                            child
                        )
                    )

                item["items"] = folder_items
                item["kind"] = "folder"

            return item

        new_sections = []

        for section_index in range(
            self.tree.topLevelItemCount()
        ):
            section_tree = self.tree.topLevelItem(
                section_index
            )

            section_id = self.item_data(
                section_tree,
                ROLE_ID
            )

            section = existing.get(
                section_id
            )

            if (
                section is None or
                "items" not in section
            ):
                section = _section({
                    "id": section_id,
                    "name": text_type(
                        section_tree.text(
                            1
                        )
                    ),
                    "label": text_type(
                        section_tree.text(
                            0
                        )
                    )
                })

            section["label"] = text_type(
                section_tree.text(
                    0
                )
            )
            section["name"] = _sanitize_internal_name(
                text_type(
                    section_tree.text(
                        1
                    )
                ),
                "folder"
            )

            new_items = []

            for child_index in range(
                section_tree.childCount()
            ):
                child = section_tree.child(
                    child_index
                )

                kind = self.item_data(
                    child,
                    ROLE_KIND
                )

                new_items.append(
                    item_from_tree(
                        child
                    )
                )

            section["items"] = new_items
            new_sections.append(
                section
            )

        self.working["sections"] = new_sections

    def tree_changed(self):
        self.sync_working_from_tree()

        self.status.setText(
            "Interface order changed. Apply or Accept to save."
        )

    # ------------------------------------------------------------------
    # Create / order / delete
    # ------------------------------------------------------------------

    def selected_section_tree_item(self):
        current = self.tree.currentItem()

        if current is None:
            if self.tree.topLevelItemCount():
                return self.tree.topLevelItem(
                    0
                )
            return None

        while current is not None:
            if self.item_data(
                current,
                ROLE_KIND
            ) == "folder":
                return current

            current = current.parent()

        return None

    def selected_row_tree_item(self):
        current = self.tree.currentItem()

        if current is None:
            return None

        if self.item_data(
            current,
            ROLE_KIND
        ) == "row":
            return current

        parent = current.parent()

        if (
            parent is not None and
            self.item_data(
                parent,
                ROLE_KIND
            ) == "row"
        ):
            return parent

        return None

    def create_from_palette(
        self,
        palette_item
    ):
        kind = palette_item.data(
            ROLE_KIND
        )

        try:
            kind = kind.toString()
        except Exception:
            pass

        kind = text_type(
            kind
        )

        self.flush_current_properties()

        if kind == "folder":
            data = _section({
                "label": "New Folder",
                "folder_type": "collapsible"
            })

            tree_item = QtGui.QTreeWidgetItem(
                [
                    data["label"],
                    data["name"],
                    "Folder"
                ]
            )

            self.set_item_data(
                tree_item,
                "folder",
                data["id"]
            )

            flags = tree_item.flags()
            flags |= QtCore.Qt.ItemIsDragEnabled
            flags |= QtCore.Qt.ItemIsDropEnabled
            tree_item.setFlags(
                flags
            )

            self.tree.addTopLevelItem(
                tree_item
            )
            tree_item.setExpanded(
                True
            )
            self.tree.setCurrentItem(
                tree_item
            )

        else:
            section_parent = self.selected_section_tree_item()

            if section_parent is None:
                section_data = _section({
                    "name": "my_tools",
                    "label": "My Tools"
                })

                section_parent = QtGui.QTreeWidgetItem(
                    [
                        section_data["label"],
                        section_data["name"],
                        "Folder"
                    ]
                )

                self.set_item_data(
                    section_parent,
                    "folder",
                    section_data["id"]
                )

                flags = section_parent.flags()
                flags &= ~QtCore.Qt.ItemIsDragEnabled
                flags |= QtCore.Qt.ItemIsDropEnabled
                section_parent.setFlags(
                    flags
                )

                self.tree.addTopLevelItem(
                    section_parent
                )

            # Row itself always belongs directly to a Section.
            if kind == "row":
                parent = section_parent
            else:
                parent = (
                    self.selected_row_tree_item() or
                    section_parent
                )

            data = _new_item_by_kind(
                kind
            )

            child = QtGui.QTreeWidgetItem(
                [
                    data["label"],
                    data["name"],
                    data["kind"].title()
                ]
            )

            self.set_item_data(
                child,
                data["kind"],
                data["id"]
            )

            flags = child.flags()
            flags |= QtCore.Qt.ItemIsDragEnabled

            if kind == "row":
                flags |= QtCore.Qt.ItemIsDropEnabled
            else:
                flags &= ~QtCore.Qt.ItemIsDropEnabled

            child.setFlags(
                flags
            )

            parent.addChild(
                child
            )
            parent.setExpanded(
                True
            )
            self.tree.setCurrentItem(
                child
            )

        self.fix_tree_structure()
        self.sync_working_from_tree()

        self.status.setText(
            "Item added. Apply or Accept to save."
        )

    def move_selected(
        self,
        direction
    ):
        current = self.tree.currentItem()

        if current is None:
            return

        self.flush_current_properties()

        parent = current.parent()

        if parent is None:
            index = self.tree.indexOfTopLevelItem(
                current
            )
            new_index = index + direction

            if (
                new_index < 0 or
                new_index >=
                self.tree.topLevelItemCount()
            ):
                return

            item = self.tree.takeTopLevelItem(
                index
            )
            self.tree.insertTopLevelItem(
                new_index,
                item
            )

        else:
            index = parent.indexOfChild(
                current
            )
            new_index = index + direction

            if (
                new_index < 0 or
                new_index >=
                parent.childCount()
            ):
                return

            item = parent.takeChild(
                index
            )
            parent.insertChild(
                new_index,
                item
            )

        self.tree.setCurrentItem(
            current
        )

        self.sync_working_from_tree()

        self.status.setText(
            "Item moved. Apply or Accept to save."
        )

    def delete_selected(self):
        current = self.tree.currentItem()

        if current is None:
            return

        kind = self.item_data(
            current,
            ROLE_KIND
        )
        name = text_type(
            current.text(0)
        )

        if kind == "folder":
            message = (
                "Delete folder '{0}' and everything inside it?"
            ).format(name)
        else:
            message = "Delete '{0}'?".format(
                name
            )

        result = QtGui.QMessageBox.question(
            self,
            "Delete Item",
            message,
            QtGui.QMessageBox.Yes |
            QtGui.QMessageBox.No,
            QtGui.QMessageBox.No
        )

        if result != QtGui.QMessageBox.Yes:
            return

        parent = current.parent()

        if parent is None:
            index = self.tree.indexOfTopLevelItem(
                current
            )
            self.tree.takeTopLevelItem(
                index
            )
        else:
            parent.removeChild(
                current
            )

        self.current_kind = None
        self.current_id = None

        self.property_stack.setCurrentWidget(
            self.empty_page
        )

        self.sync_working_from_tree()

        self.status.setText(
            "Item deleted. Apply or Accept to save."
        )

    # ------------------------------------------------------------------
    # Critical selection bug fix
    # ------------------------------------------------------------------

    def selection_changed(
        self,
        current,
        previous
    ):
        # IMPORTANT:
        # Save the OLD item before changing self.current_id.
        # flush_current_properties() updates the tree row by the OLD id,
        # never by self.tree.currentItem(). This prevents names from
        # leaking from the previous item into the newly selected row.
        if self.current_id:
            self.flush_current_properties()

        if current is None:
            self.current_kind = None
            self.current_id = None
            self.property_stack.setCurrentWidget(
                self.empty_page
            )
            return

        new_kind = self.item_data(
            current,
            ROLE_KIND
        )
        new_id = self.item_data(
            current,
            ROLE_ID
        )

        self.current_kind = new_kind
        self.current_id = new_id

        data = self.find_data(
            new_id
        )

        if data is None:
            self.sync_working_from_tree()
            data = self.find_data(
                new_id
            )

        if data is not None:
            self.load_properties(
                new_kind,
                data
            )

    # ------------------------------------------------------------------
    # Load / flush properties
    # ------------------------------------------------------------------

    def load_properties(
        self,
        kind,
        data
    ):
        self.loading_properties = True

        try:
            if kind == "folder":
                self.section_internal_name.setText(
                    data.get(
                        "name",
                        ""
                    )
                )
                self.section_label.setText(
                    data.get(
                        "label",
                        data.get(
                            "name",
                            ""
                        )
                    )
                )
                self.section_show_label.setChecked(
                    bool(
                        data.get(
                            "show_label",
                            True
                        )
                    )
                )

                folder_type = data.get(
                    "folder_type",
                    "collapsible"
                )

                folder_index = {
                    "collapsible": 0,
                    "simple": 1,
                    "tabs": 2,
                    "radio": 3
                }.get(
                    folder_type,
                    0
                )

                self.section_folder_type.setCurrentIndex(
                    folder_index
                )
                self.section_collapsed.setChecked(
                    bool(
                        data.get(
                            "collapsed",
                            False
                        )
                    )
                )

                self.folder_type_changed()

                self.property_stack.setCurrentIndex(
                    self.PAGE_FOLDER
                )

            elif kind == "button":
                self.button_internal_name.setText(
                    data.get("name", "")
                )
                self.button_label.setText(
                    data.get(
                        "label",
                        data.get("name", "")
                    )
                )
                self.button_show_label.setChecked(
                    bool(data.get("show_label", True))
                )
                self.button_tooltip.setText(
                    data.get("tooltip", "")
                )
                self.button_language.setCurrentIndex(
                    1
                    if data.get("language") == "mel"
                    else 0
                )
                self.click_editor.setPlainText(
                    data.get("click_script", "")
                )
                self.shift_editor.setPlainText(
                    data.get("shift_script", "")
                )

                self.current_button_color = _safe_color(
                    data.get("color")
                )
                self.refresh_button_color()
                self.language_changed()

                self.property_stack.setCurrentIndex(
                    self.PAGE_BUTTON
                )

            elif kind == "string":
                self.string_internal_name.setText(
                    data["name"]
                )
                self.string_label.setText(
                    data.get("label", data["name"])
                )
                self.string_show_label.setChecked(
                    bool(data.get("show_label", True))
                )
                self.string_value.setText(
                    text_type(
                        data.get("value", "")
                    )
                )
                self.string_tooltip.setText(
                    data.get("tooltip", "")
                )
                self.property_stack.setCurrentIndex(
                    self.PAGE_STRING
                )

            elif kind == "integer":
                self.integer_internal_name.setText(
                    data["name"]
                )
                self.integer_label.setText(
                    data.get("label", data["name"])
                )
                self.integer_show_label.setChecked(
                    bool(data.get("show_label", True))
                )
                self.integer_min.setValue(data["min"])
                self.integer_max.setValue(data["max"])
                self.integer_step.setValue(data["step"])
                self.integer_value.setValue(data["value"])
                self.integer_tooltip.setText(
                    data.get("tooltip", "")
                )
                self.property_stack.setCurrentIndex(
                    self.PAGE_INTEGER
                )

            elif kind == "float":
                self.float_internal_name.setText(
                    data["name"]
                )
                self.float_label.setText(
                    data.get("label", data["name"])
                )
                self.float_show_label.setChecked(
                    bool(data.get("show_label", True))
                )
                self.float_min.setValue(data["min"])
                self.float_max.setValue(data["max"])
                self.float_step.setValue(data["step"])
                self.float_decimals.setValue(
                    data["decimals"]
                )
                self.float_value.setValue(data["value"])
                self.float_tooltip.setText(
                    data.get("tooltip", "")
                )
                self.property_stack.setCurrentIndex(
                    self.PAGE_FLOAT
                )

            elif kind == "toggle":
                # Legacy in-memory fallback: present it as Checkbox/Left.
                legacy = _toggle_item(
                    data
                )

                self.checkbox_internal_name.setText(
                    legacy["name"]
                )
                self.checkbox_label.setText(
                    legacy.get(
                        "label",
                        legacy["name"]
                    )
                )
                self.checkbox_show_label.setChecked(
                    bool(
                        legacy.get(
                            "show_label",
                            True
                        )
                    )
                )
                self.checkbox_label_position.setCurrentIndex(
                    1
                )
                self.checkbox_value.setChecked(
                    bool(
                        legacy.get(
                            "value",
                            False
                        )
                    )
                )
                self.checkbox_tooltip.setText(
                    legacy.get(
                        "tooltip",
                        ""
                    )
                )

                self.property_stack.setCurrentIndex(
                    self.PAGE_CHECKBOX
                )

            elif kind == "checkbox":
                self.checkbox_internal_name.setText(
                    data["name"]
                )
                self.checkbox_label.setText(
                    data.get(
                        "label",
                        data["name"]
                    )
                )
                self.checkbox_show_label.setChecked(
                    bool(
                        data.get(
                            "show_label",
                            True
                        )
                    )
                )
                self.checkbox_label_position.setCurrentIndex(
                    1
                    if data.get(
                        "label_position",
                        "right"
                    ) == "left"
                    else 0
                )
                self.checkbox_value.setChecked(
                    bool(
                        data.get(
                            "value",
                            False
                        )
                    )
                )
                self.checkbox_tooltip.setText(
                    data.get(
                        "tooltip",
                        ""
                    )
                )

                self.property_stack.setCurrentIndex(
                    self.PAGE_CHECKBOX
                )

            elif kind == "menu":
                self.menu_internal_name.setText(
                    data["name"]
                )
                self.menu_label.setText(
                    data.get("label", data["name"])
                )
                self.menu_show_label.setChecked(
                    bool(data.get("show_label", True))
                )
                self.menu_tooltip.setText(
                    data.get("tooltip", "")
                )
                self.menu_items.setPlainText(
                    "\n".join(data["items"])
                )
                self.rebuild_menu_value_combo(
                    data["items"],
                    data["value"]
                )
                self.property_stack.setCurrentIndex(
                    self.PAGE_MENU
                )

            elif kind == "color":
                self.color_internal_name.setText(
                    data["name"]
                )
                self.color_label.setText(
                    data.get("label", data["name"])
                )
                self.color_show_label.setChecked(
                    bool(data.get("show_label", True))
                )
                self.color_tooltip.setText(
                    data.get("tooltip", "")
                )
                self.current_param_color = _safe_color(
                    data.get("value")
                )
                self.refresh_param_color()
                self.property_stack.setCurrentIndex(
                    self.PAGE_COLOR
                )

            elif kind == "label":
                self.label_internal_name.setText(
                    data["name"]
                )
                self.label_label.setText(
                    data.get("label", data["name"])
                )
                self.label_show_label.setChecked(
                    bool(data.get("show_label", True))
                )
                self.label_tooltip.setText(
                    data.get("tooltip", "")
                )
                self.property_stack.setCurrentIndex(
                    self.PAGE_LABEL
                )

            elif kind == "field":
                self.field_internal_name.setText(
                    data["name"]
                )
                self.field_label.setText(
                    data.get(
                        "label",
                        data["name"]
                    )
                )
                self.field_show_label.setChecked(
                    bool(data.get("show_label", True))
                )

                self.field_source.setCurrentIndex(
                    1
                    if data.get(
                        "source"
                    ) == "selection"
                    else 0
                )

                value = data.get(
                    "value",
                    ""
                )

                if isinstance(
                    value,
                    (list, tuple)
                ):
                    value_text = ", ".join(
                        text_type(item)
                        for item in value
                    )
                else:
                    value_text = text_type(
                        value
                    )

                self.field_value.setText(
                    value_text
                )
                self.field_placeholder.setText(
                    data.get(
                        "placeholder",
                        ""
                    )
                )
                self.field_selectable.setChecked(
                    bool(
                        data.get(
                            "selectable",
                            True
                        )
                    )
                )
                self.field_select_scene.setChecked(
                    bool(
                        data.get(
                            "select_scene",
                            False
                        )
                    )
                )
                self.field_multiple.setChecked(
                    bool(
                        data.get(
                            "multiple",
                            True
                        )
                    )
                )
                self.field_long_names.setChecked(
                    bool(
                        data.get(
                            "long_names",
                            False
                        )
                    )
                )
                self.field_tooltip.setText(
                    data.get(
                        "tooltip",
                        ""
                    )
                )

                self.field_source_changed()

                self.property_stack.setCurrentIndex(
                    self.PAGE_FIELD
                )

            elif kind == "row":
                self.row_internal_name.setText(
                    data["name"]
                )
                self.row_label.setText(
                    data.get(
                        "label",
                        data["name"]
                    )
                )
                self.row_show_label.setChecked(
                    bool(data.get("show_label", True))
                )
                self.row_spacing.setValue(
                    int(
                        data.get(
                            "spacing",
                            4
                        )
                    )
                )

                self.property_stack.setCurrentIndex(
                    self.PAGE_ROW
                )

            elif kind == "separator":
                self.separator_internal_name.setText(
                    data["name"]
                )
                self.separator_label.setText(
                    data.get("label", data["name"])
                )
                self.separator_show_label.setChecked(
                    bool(data.get("show_label", True))
                )
                self.property_stack.setCurrentIndex(
                    self.PAGE_SEPARATOR
                )

            else:
                self.property_stack.setCurrentIndex(
                    self.PAGE_EMPTY
                )

        finally:
            self.loading_properties = False
    def flush_current_properties(self):
        if (
            self.loading_properties or
            not self.current_id
        ):
            return

        data = self.find_data(
            self.current_id
        )

        if data is None:
            return

        kind = self.current_kind

        if kind == "folder":
            data["name"] = _sanitize_internal_name(
                text_type(
                    self.section_internal_name.text()
                ),
                "folder"
            )
            data["label"] = (
                text_type(
                    self.section_label.text()
                ).strip() or
                data["name"]
            )
            data["show_label"] = bool(
                self.section_show_label.isChecked()
            )

            folder_type = (
                "collapsible"
                if self.section_folder_type.currentIndex() == 0
                else "simple"
                if self.section_folder_type.currentIndex() == 1
                else "tabs"
                if self.section_folder_type.currentIndex() == 2
                else "radio"
            )

            data["folder_type"] = folder_type
            data["collapsed"] = (
                bool(
                    self.section_collapsed.isChecked()
                )
                if folder_type == "collapsible"
                else False
            )

        elif kind == "button":
            data["name"] = _sanitize_internal_name(
                text_type(
                    self.button_internal_name.text()
                ),
                "button"
            )
            data["label"] = (
                text_type(
                    self.button_label.text()
                ).strip() or
                data["name"]
            )
            data["show_label"] = bool(
                self.button_show_label.isChecked()
            )
            data["tooltip"] = text_type(
                self.button_tooltip.text()
            )
            data["language"] = (
                "mel"
                if self.button_language.currentIndex() == 1
                else "python"
            )
            data["click_script"] = text_type(
                self.click_editor.toPlainText()
            )
            data["shift_script"] = text_type(
                self.shift_editor.toPlainText()
            )
            data["color"] = list(
                self.current_button_color
            )

        elif kind == "string":
            data["name"] = _sanitize_internal_name(
                text_type(
                    self.string_internal_name.text()
                ),
                "string"
            )
            data["label"] = (
                text_type(
                    self.string_label.text()
                ).strip() or
                data["name"]
            )
            data["show_label"] = bool(
                self.string_show_label.isChecked()
            )
            data["value"] = text_type(
                self.string_value.text()
            )
            data["tooltip"] = text_type(
                self.string_tooltip.text()
            )

        elif kind == "integer":
            minimum = int(
                self.integer_min.value()
            )
            maximum = int(
                self.integer_max.value()
            )

            if minimum > maximum:
                minimum, maximum = (
                    maximum,
                    minimum
                )

            data["name"] = _sanitize_internal_name(
                text_type(
                    self.integer_internal_name.text()
                ),
                "integer"
            )
            data["label"] = (
                text_type(
                    self.integer_label.text()
                ).strip() or
                data["name"]
            )
            data["show_label"] = bool(
                self.integer_show_label.isChecked()
            )
            data["min"] = minimum
            data["max"] = maximum
            data["step"] = max(
                1,
                int(
                    self.integer_step.value()
                )
            )
            data["value"] = _clamp(
                int(
                    self.integer_value.value()
                ),
                minimum,
                maximum
            )
            data["tooltip"] = text_type(
                self.integer_tooltip.text()
            )

        elif kind == "float":
            minimum = float(
                self.float_min.value()
            )
            maximum = float(
                self.float_max.value()
            )

            if minimum > maximum:
                minimum, maximum = (
                    maximum,
                    minimum
                )

            data["name"] = _sanitize_internal_name(
                text_type(
                    self.float_internal_name.text()
                ),
                "float"
            )
            data["label"] = (
                text_type(
                    self.float_label.text()
                ).strip() or
                data["name"]
            )
            data["show_label"] = bool(
                self.float_show_label.isChecked()
            )
            data["min"] = minimum
            data["max"] = maximum
            data["step"] = max(
                0.000001,
                float(
                    self.float_step.value()
                )
            )
            data["decimals"] = int(
                self.float_decimals.value()
            )
            data["value"] = _clamp(
                float(
                    self.float_value.value()
                ),
                minimum,
                maximum
            )
            data["tooltip"] = text_type(
                self.float_tooltip.text()
            )

        elif kind == "toggle":
            # Convert any legacy Toggle edited in-memory to canonical Checkbox.
            data["kind"] = "checkbox"
            data["name"] = _sanitize_internal_name(
                text_type(
                    self.checkbox_internal_name.text()
                ),
                "checkbox"
            )
            data["label"] = (
                text_type(
                    self.checkbox_label.text()
                ).strip() or
                data["name"]
            )
            data["show_label"] = bool(
                self.checkbox_show_label.isChecked()
            )
            data["label_position"] = (
                "left"
                if self.checkbox_label_position.currentIndex() == 1
                else "right"
            )
            data["value"] = bool(
                self.checkbox_value.isChecked()
            )
            data["tooltip"] = text_type(
                self.checkbox_tooltip.text()
            )

        elif kind == "checkbox":
            data["name"] = _sanitize_internal_name(
                text_type(
                    self.checkbox_internal_name.text()
                ),
                "checkbox"
            )
            data["label"] = (
                text_type(
                    self.checkbox_label.text()
                ).strip() or
                data["name"]
            )
            data["show_label"] = bool(
                self.checkbox_show_label.isChecked()
            )
            data["label_position"] = (
                "left"
                if self.checkbox_label_position.currentIndex() == 1
                else "right"
            )
            data["value"] = bool(
                self.checkbox_value.isChecked()
            )
            data["tooltip"] = text_type(
                self.checkbox_tooltip.text()
            )

        elif kind == "menu":
            items = _safe_menu_items(
                text_type(
                    self.menu_items.toPlainText()
                )
            )

            value = text_type(
                self.menu_value.currentText()
            )

            if value not in items:
                value = items[0]

            data["name"] = _sanitize_internal_name(
                text_type(
                    self.menu_internal_name.text()
                ),
                "menu"
            )
            data["label"] = (
                text_type(
                    self.menu_label.text()
                ).strip() or
                data["name"]
            )
            data["show_label"] = bool(
                self.menu_show_label.isChecked()
            )
            data["items"] = items
            data["value"] = value
            data["tooltip"] = text_type(
                self.menu_tooltip.text()
            )

        elif kind == "color":
            data["name"] = _sanitize_internal_name(
                text_type(
                    self.color_internal_name.text()
                ),
                "color"
            )
            data["label"] = (
                text_type(
                    self.color_label.text()
                ).strip() or
                data["name"]
            )
            data["show_label"] = bool(
                self.color_show_label.isChecked()
            )
            data["value"] = list(
                self.current_param_color
            )
            data["tooltip"] = text_type(
                self.color_tooltip.text()
            )

        elif kind == "label":
            data["name"] = _sanitize_internal_name(
                text_type(
                    self.label_internal_name.text()
                ),
                "label"
            )
            data["label"] = (
                text_type(
                    self.label_label.text()
                ).strip() or
                data["name"]
            )
            data["show_label"] = bool(
                self.label_show_label.isChecked()
            )
            data["tooltip"] = text_type(
                self.label_tooltip.text()
            )

        elif kind == "field":
            data["name"] = _sanitize_internal_name(
                text_type(
                    self.field_internal_name.text()
                ),
                "field"
            )
            data["label"] = (
                text_type(
                    self.field_label.text()
                ).strip() or
                data["name"]
            )

            data["source"] = (
                "selection"
                if self.field_source.currentIndex() == 1
                else "value"
            )

            if data["source"] == "value":
                data["value"] = text_type(
                    self.field_value.text()
                )

            data["show_label"] = bool(
                self.field_show_label.isChecked()
            )
            data["placeholder"] = text_type(
                self.field_placeholder.text()
            )
            data["selectable"] = bool(
                self.field_selectable.isChecked()
            )
            data["select_scene"] = bool(
                self.field_select_scene.isChecked()
            )
            data["multiple"] = bool(
                self.field_multiple.isChecked()
            )
            data["long_names"] = bool(
                self.field_long_names.isChecked()
            )
            data["tooltip"] = text_type(
                self.field_tooltip.text()
            )

        elif kind == "row":
            data["name"] = _sanitize_internal_name(
                text_type(
                    self.row_internal_name.text()
                ),
                "row"
            )
            data["label"] = (
                text_type(
                    self.row_label.text()
                ).strip() or
                data["name"]
            )
            data["show_label"] = bool(
                self.row_show_label.isChecked()
            )
            data["spacing"] = int(
                self.row_spacing.value()
            )

        elif kind == "separator":
            data["name"] = _sanitize_internal_name(
                text_type(
                    self.separator_internal_name.text()
                ),
                "separator"
            )
            data["label"] = (
                text_type(
                    self.separator_label.text()
                ).strip() or
                data["name"]
            )
            data["show_label"] = bool(
                self.separator_show_label.isChecked()
            )

        # Important selection bug fix:
        # update the row by stored ID, not by currentItem().
        tree_item = self.tree_item_by_id(
            self.current_id
        )

        if tree_item is not None:
            tree_item.setText(
                0,
                data.get(
                    "label",
                    data.get("name", "")
                )
            )
            tree_item.setText(
                1,
                data.get("name", "")
            )

    # ------------------------------------------------------------------
    # Property callbacks
    # ------------------------------------------------------------------

    def property_edited(
        self,
        *args
    ):
        if self.loading_properties:
            return

        self.flush_current_properties()

        self.status.setText(
            "Properties changed. Apply or Accept to save."
        )

    def language_changed(
        self,
        *args
    ):
        language = (
            "mel"
            if self.button_language.currentIndex() == 1
            else "python"
        )

        self.click_highlighter.set_language(
            language
        )
        self.shift_highlighter.set_language(
            language
        )

        self.code_update_cursor_position()

        if not self.loading_properties:
            self.property_edited()

    # ------------------------------------------------------------------
    # Embedded Houdini-like code editor helpers
    # ------------------------------------------------------------------

    def current_code_editor(self):
        if self.code_tabs.currentIndex() == 1:
            return self.shift_editor
        return self.click_editor

    def current_code_text(self):
        return text_type(
            self.current_code_editor().toPlainText()
        )

    def code_undo(self):
        self.current_code_editor().undo()

    def code_redo(self):
        self.current_code_editor().redo()

    def code_cut(self):
        self.current_code_editor().cut()

    def code_copy(self):
        self.current_code_editor().copy()

    def code_paste(self):
        self.current_code_editor().paste()

    def code_update_cursor_position(self, *args):
        try:
            cursor = self.current_code_editor().textCursor()

            self.code_cursor_label.setText(
                "Ln {0}, Col {1}".format(
                    cursor.blockNumber() + 1,
                    cursor.columnNumber() + 1
                )
            )
        except Exception:
            pass

    def code_find(self):
        value, ok = QtGui.QInputDialog.getText(
            self,
            "Find",
            "Find:"
        )

        if not ok:
            return

        value = text_type(value)

        if not value:
            return

        self._last_code_find = value

        editor = self.current_code_editor()

        if not editor.find(value):
            cursor = editor.textCursor()
            cursor.movePosition(
                QtGui.QTextCursor.Start
            )
            editor.setTextCursor(cursor)

            if not editor.find(value):
                self.code_status_label.setText(
                    "Not found: {0}".format(
                        value
                    )
                )
                return

        self.code_status_label.setText(
            "Found: {0}".format(
                value
            )
        )

    def code_find_next(self):
        if not self._last_code_find:
            self.code_find()
            return

        editor = self.current_code_editor()

        if not editor.find(
            self._last_code_find
        ):
            cursor = editor.textCursor()
            cursor.movePosition(
                QtGui.QTextCursor.Start
            )
            editor.setTextCursor(
                cursor
            )
            editor.find(
                self._last_code_find
            )

    def _selected_code_blocks(self):
        editor = self.current_code_editor()
        cursor = editor.textCursor()

        start = cursor.selectionStart()
        end = cursor.selectionEnd()

        document = editor.document()

        start_block = document.findBlock(
            start
        )
        end_block = document.findBlock(
            end
        )

        if (
            end > start and
            end_block.position() == end
        ):
            end_block = end_block.previous()

        return (
            editor,
            cursor,
            start_block,
            end_block
        )

    def _transform_code_lines(
        self,
        transform
    ):
        (
            editor,
            original_cursor,
            start_block,
            end_block
        ) = self._selected_code_blocks()

        if not start_block.isValid():
            return

        had_selection = original_cursor.hasSelection()

        start_pos = start_block.position()

        if end_block.isValid():
            end_pos = (
                end_block.position() +
                end_block.length() - 1
            )
        else:
            end_pos = start_pos

        cursor = QtGui.QTextCursor(
            editor.document()
        )

        cursor.setPosition(
            start_pos
        )

        cursor.setPosition(
            end_pos,
            QtGui.QTextCursor.KeepAnchor
        )

        selected = text_type(
            cursor.selectedText()
        ).replace(
            u"\u2029",
            "\n"
        )

        lines = selected.split(
            "\n"
        )

        new_text = "\n".join(
            transform(line)
            for line in lines
        )

        cursor.beginEditBlock()
        cursor.insertText(
            new_text
        )
        cursor.endEditBlock()

        if had_selection:
            cursor.setPosition(
                start_pos
            )
            cursor.setPosition(
                start_pos + len(new_text),
                QtGui.QTextCursor.KeepAnchor
            )

        editor.setTextCursor(
            cursor
        )

    def code_comment(self):
        marker = (
            "// "
            if self.button_language.currentIndex() == 1
            else "# "
        )

        def transform(line):
            if not line.strip():
                return line

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

        self._transform_code_lines(
            transform
        )

    def code_uncomment(self):
        marker = (
            "//"
            if self.button_language.currentIndex() == 1
            else "#"
        )

        def transform(line):
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

        self._transform_code_lines(
            transform
        )

    def code_indent(self):
        self._transform_code_lines(
            lambda line: "    " + line
        )

    def code_unindent(self):
        def transform(line):
            if line.startswith("    "):
                return line[4:]

            if line.startswith("\t"):
                return line[1:]

            spaces = (
                len(line) -
                len(line.lstrip(" "))
            )

            return line[
                min(4, spaces):
            ]

        self._transform_code_lines(
            transform
        )

    def code_append_output(
        self,
        value
    ):
        if value is None:
            return

        value = text_type(value)

        if not value:
            return

        self.code_output.moveCursor(
            QtGui.QTextCursor.End
        )

        self.code_output.insertPlainText(
            value
        )

        if not value.endswith("\n"):
            self.code_output.insertPlainText(
                "\n"
            )

        self.code_output.moveCursor(
            QtGui.QTextCursor.End
        )

    def code_run(self):
        code = self.current_code_text()

        self.code_output.clear()
        self.code_status_label.setText(
            "Running..."
        )

        if not code.strip():
            self.code_status_label.setText(
                "Nothing to run"
            )
            return

        language = (
            "mel"
            if self.button_language.currentIndex() == 1
            else "python"
        )

        if language == "mel":
            try:
                result = mel.eval(
                    code
                )

                if result is not None:
                    self.code_append_output(
                        result
                    )

                if not self.code_output.toPlainText():
                    self.code_append_output(
                        "Finished without output."
                    )

                self.code_status_label.setText(
                    "Finished"
                )

            except Exception:
                self.code_append_output(
                    traceback.format_exc()
                )
                self.code_status_label.setText(
                    "Error"
                )

            return

        old_stdout = sys.stdout
        old_stderr = sys.stderr

        stdout_buffer = StringIO()
        stderr_buffer = StringIO()

        namespace = {
            "__name__": "__maya_script_toolbox_editor__",
            "cmds": cmds,
            "mel": mel,
            "toolbox": self.toolbox
        }

        try:
            sys.stdout = stdout_buffer
            sys.stderr = stderr_buffer

            compiled = compile(
                code,
                "<Maya Script Toolbox Editor>",
                "exec"
            )

            eval(
                compiled,
                namespace,
                namespace
            )

            self.code_status_label.setText(
                "Finished"
            )

        except Exception:
            traceback.print_exc()
            self.code_status_label.setText(
                "Error"
            )

        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        stdout_value = stdout_buffer.getvalue()
        stderr_value = stderr_buffer.getvalue()

        if stdout_value:
            self.code_append_output(
                stdout_value
            )

        if stderr_value:
            self.code_append_output(
                stderr_value
            )

        if (
            not stdout_value and
            not stderr_value
        ):
            self.code_append_output(
                "Finished without output."
            )

    def menu_items_edited(self):
        if self.loading_properties:
            return

        current = text_type(
            self.menu_value.currentText()
        )

        items = _safe_menu_items(
            text_type(
                self.menu_items.toPlainText()
            )
        )

        self.loading_properties = True
        try:
            self.rebuild_menu_value_combo(
                items,
                current
            )
        finally:
            self.loading_properties = False

        self.property_edited()

    def rebuild_menu_value_combo(
        self,
        items,
        current
    ):
        self.menu_value.clear()
        self.menu_value.addItems(
            items
        )

        index = self.menu_value.findText(
            current
        )

        if index < 0:
            index = 0

        self.menu_value.setCurrentIndex(
            index
        )

    def choose_button_color(self):
        initial = QtGui.QColor(
            int(
                self.current_button_color[0] *
                255
            ),
            int(
                self.current_button_color[1] *
                255
            ),
            int(
                self.current_button_color[2] *
                255
            )
        )

        color = QtGui.QColorDialog.getColor(
            initial,
            self,
            "Button Color"
        )

        if not color.isValid():
            return

        self.current_button_color = [
            color.red() / 255.0,
            color.green() / 255.0,
            color.blue() / 255.0
        ]

        self.refresh_button_color()
        self.property_edited()

    def refresh_button_color(self):
        rgb = [
            int(value * 255)
            for value in self.current_button_color        ]

        self.button_color.setStyleSheet(
            "QPushButton {"
            "background-color: rgb(%d,%d,%d);"
            "}" % (
                rgb[0],
                rgb[1],
                rgb[2]
            )
        )

    def choose_param_color(self):
        initial = QtGui.QColor(
            int(
                self.current_param_color[0] *
                255
            ),
            int(
                self.current_param_color[1] *
                255
            ),
            int(
                self.current_param_color[2] *
                255
            )
        )

        color = QtGui.QColorDialog.getColor(
            initial,
            self,
            "Color Value"
        )

        if not color.isValid():
            return

        self.current_param_color = [
            color.red() / 255.0,
            color.green() / 255.0,
            color.blue() / 255.0
        ]

        self.refresh_param_color()
        self.property_edited()

    def refresh_param_color(self):
        rgb = [
            int(value * 255)
            for value in self.current_param_color
        ]

        self.color_value.setStyleSheet(
            "QPushButton {"
            "background-color: rgb(%d,%d,%d);"
            "}" % (
                rgb[0],
                rgb[1],
                rgb[2]
            )
        )

    # ------------------------------------------------------------------
    # Button tests
    # ------------------------------------------------------------------

    def test_click(self):
        self.flush_current_properties()

        data = self.find_data(
            self.current_id
        )

        if (
            not data or
            data.get("kind") != "button"
        ):
            return

        execute_script(
            data.get(
                "click_script",
                ""
            ),
            data.get(
                "language",
                "python"
            ),
            parent=self,
            toolbox=self.toolbox
        )

    def test_shift(self):
        self.flush_current_properties()

        data = self.find_data(
            self.current_id
        )

        if (
            not data or
            data.get("kind") != "button"
        ):
            return

        code = data.get(
            "shift_script",
            ""
        )

        if not code.strip():
            code = data.get(
                "click_script",
                ""
            )

        execute_script(
            code,
            data.get(
                "language",
                "python"
            ),
            parent=self,
            toolbox=self.toolbox
        )

    # ------------------------------------------------------------------
    # Import / Export settings
    # ------------------------------------------------------------------

    def _dialog_path(
        self,
        result
    ):
        """
        QFileDialog returns either a string or a (filename, filter) tuple
        depending on the Qt/PySide build.
        """
        if isinstance(
            result,
            (tuple, list)
        ):
            if not result:
                return ""

            result = result[
                0
            ]

        try:
            result = result.toString()
        except Exception:
            pass

        return text_type(
            result or ""
        )

    def export_settings(self):
        self.sync_working_from_tree()

        if not self.validate_internal_names():
            return

        default_path = os.path.join(
            os.path.dirname(
                _config_path()
            ),
            "maya_script_toolbox_export.json"
        )

        result = QtGui.QFileDialog.getSaveFileName(
            self,
            "Export Toolbox Settings",
            default_path,
            "JSON Files (*.json);;All Files (*.*)"
        )

        path = self._dialog_path(
            result
        )

        if not path:
            return

        if not path.lower().endswith(
            ".json"
        ):
            path += ".json"

        try:
            payload = normalize_config(
                copy.deepcopy(
                    self.working
                )
            )

            with io.open(
                path,
                "w",
                encoding="utf-8"
            ) as handle:
                handle.write(
                    text_type(
                        json.dumps(
                            payload,
                            ensure_ascii=False,
                            indent=2
                        )
                    )
                )

            self.status.setText(
                "Exported: {0}".format(
                    os.path.basename(
                        path
                    )
                )
            )

        except Exception:
            error_text = traceback.format_exc()
            print(
                error_text
            )

            box = QtGui.QMessageBox(
                self
            )
            box.setWindowTitle(
                "Export Failed"
            )
            box.setIcon(
                QtGui.QMessageBox.Critical
            )
            box.setText(
                "Could not export Toolbox settings."
            )
            box.setDetailedText(
                error_text
            )
            box.exec_()

    def import_settings(self):
        result = QtGui.QFileDialog.getOpenFileName(
            self,
            "Import Toolbox Settings",
            os.path.dirname(
                _config_path()
            ),
            "JSON Files (*.json);;All Files (*.*)"
        )

        path = self._dialog_path(
            result
        )

        if not path:
            return

        try:
            with io.open(
                path,
                "r",
                encoding="utf-8"
            ) as handle:
                raw = json.load(
                    handle
                )

            imported = normalize_config(
                raw
            )

            # Replace only the staged editor state.
            # Live config is not touched until Apply / Accept.
            self.current_kind = None
            self.current_id = None
            self.working = copy.deepcopy(
                imported
            )

            self.populate_tree()

            self.status.setText(
                "Imported {0}. Apply or Accept to save.".format(
                    os.path.basename(
                        path
                    )
                )
            )

        except Exception:
            error_text = traceback.format_exc()
            print(
                error_text
            )

            box = QtGui.QMessageBox(
                self
            )
            box.setWindowTitle(
                "Import Failed"
            )
            box.setIcon(
                QtGui.QMessageBox.Critical
            )
            box.setText(
                "Could not import Toolbox settings."
            )
            box.setDetailedText(
                error_text
            )
            box.exec_()


    # ------------------------------------------------------------------
    # Name validation
    # ------------------------------------------------------------------

    def validate_internal_names(self):
        section_names = {}
        item_names = {}

        def validate_items(
            items
        ):
            for item in items:
                item_name = item.get(
                    "name",
                    ""
                )

                if item_name in item_names:
                    QtGui.QMessageBox.warning(
                        self,
                        "Duplicate Name",
                        "Item Name '{0}' is used more than once.\\n\\n"
                        "Names are script identifiers and must be unique.".format(
                            item_name
                        )
                    )
                    return False

                item_names[
                    item_name
                ] = True

                if item.get(
                    "kind"
                ) in (
                    "row",
                    "folder"
                ):
                    if not validate_items(
                        item.get(
                            "items",
                            []
                        )
                    ):
                        return False

            return True

        for section in self.working["sections"]:
            section_name = section.get(
                "name",
                ""
            )

            if section_name in section_names:
                QtGui.QMessageBox.warning(
                    self,
                    "Duplicate Name",
                    "Folder Name '{0}' is used more than once.".format(
                        section_name
                    )
                )
                return False

            section_names[
                section_name
            ] = True

            if not validate_items(
                section["items"]
            ):
                return False

        return True

    # ------------------------------------------------------------------
    # Apply / Accept
    # ------------------------------------------------------------------

    def apply_changes(self):
        self.sync_working_from_tree()

        if not self.validate_internal_names():
            return

        self.toolbox.config = normalize_config(
            copy.deepcopy(
                self.working
            )
        )

        self.toolbox.save()
        self.toolbox.rebuild()

        self.working = copy.deepcopy(
            self.toolbox.config
        )

        self.status.setText(
            "Applied."
        )

    def accept_changes(self):
        self.apply_changes()
        self.accept()


# ----------------------------------------------------------------------
# Main toolbox
# ----------------------------------------------------------------------

class ScriptToolbox(QtGui.QMainWindow):

    def __init__(
        self,
        parent=None
    ):
        QtGui.QMainWindow.__init__(
            self,
            parent or maya_main_window()
        )

        self.setObjectName(
            WINDOW_OBJECT_NAME
        )
        self.setWindowTitle(
            "Script Toolbox"
        )
        self.resize(
            420,
            700
        )
        self.setMinimumWidth(
            310
        )
        self.setStyleSheet(
            STYLE
        )

        self.config = load_config()
        self.editor_window = None

        self.field_widgets = {}
        self._selection_signature = None

        self.build_ui()
        self.rebuild()

        self.selection_timer = QtCore.QTimer(
            self
        )
        self.selection_timer.setInterval(
            300
        )
        self.selection_timer.timeout.connect(
            self.refresh_selection_fields
        )
        self.selection_timer.start()

    def build_ui(self):
        central = QtGui.QWidget()
        central.setObjectName(
            "ToolboxCentral"
        )
        self.setCentralWidget(
            central
        )

        root = QtGui.QVBoxLayout(
            central
        )
        root.setContentsMargins(
            0,
            0,
            0,
            0
        )
        root.setSpacing(0)

        topbar = QtGui.QFrame()
        topbar.setObjectName(
            "TopBar"
        )

        top_layout = QtGui.QHBoxLayout(
            topbar
        )
        top_layout.setContentsMargins(
            6,
            4,
            6,
            4
        )
        top_layout.setSpacing(4)

        title = QtGui.QLabel(
            "SCRIPT TOOLBOX"
        )
        title.setObjectName(
            "ToolboxTitle"
        )

        top_layout.addWidget(
            title
        )
        top_layout.addStretch(1)

        reload_button = QtGui.QToolButton()
        reload_button.setObjectName(
            "IconButton"
        )
        reload_button.setIcon(
            _toolbar_icon("reload")
        )
        reload_button.setIconSize(
            QtCore.QSize(18, 18)
        )
        reload_button.setFixedSize(
            28,
            28
        )
        reload_button.setToolTip(
            "Reload toolbox config"
        )
        reload_button.clicked.connect(
            self.reload_config
        )

        gear = QtGui.QToolButton()
        gear.setObjectName(
            "IconButton"
        )
        gear.setIcon(
            _toolbar_icon("gear")
        )
        gear.setIconSize(
            QtCore.QSize(18, 18)
        )
        gear.setToolTip(
            "Edit Interface"
        )
        gear.setFixedSize(
            28,
            28
        )
        gear.clicked.connect(
            self.open_interface_editor
        )

        top_layout.addWidget(
            reload_button
        )
        top_layout.addWidget(
            gear
        )

        root.addWidget(
            topbar
        )

        self.scroll = QtGui.QScrollArea()
        self.scroll.setObjectName(
            "ToolboxScroll"
        )
        self.scroll.setWidgetResizable(
            True
        )

        # Qt4 can paint QScrollArea's viewport with the native system palette
        # even when the scroll area itself is styled. Set the viewport
        # explicitly without touching checkbox/radio styles.
        self.scroll.viewport().setStyleSheet(
            "background-color: #2b2b2b;"
        )

        self.content = QtGui.QWidget()
        self.content.setObjectName(
            "ToolboxContent"
        )
        self.content_layout = QtGui.QVBoxLayout(
            self.content
        )
        self.content_layout.setContentsMargins(
            6,
            6,
            6,
            6
        )
        self.content_layout.setSpacing(
            5
        )

        self.content_layout.addStretch(
            1
        )

        self.scroll.setWidget(
            self.content
        )

        root.addWidget(
            self.scroll,
            1
        )

        self.statusBar().showMessage(
            "Click = script | Shift+Click = alternate script | Name = script ID"
        )

    # ------------------------------------------------------------------
    # Config / runtime value API
    # ------------------------------------------------------------------

    def save(self):
        save_config(
            self.config
        )

    def all_items(self):
        def recurse(
            items
        ):
            for item in items:
                yield item

                if item.get(
                    "kind"
                ) in (
                    "row",
                    "folder"
                ):
                    for child in recurse(
                        item.get(
                            "items",
                            []
                        )
                    ):
                        yield child

        for section in self.config["sections"]:
            for item in recurse(
                section["items"]
            ):
                yield item

    def find_item(
        self,
        key
    ):
        key_text = text_type(
            key
        )

        # ID takes priority.
        for item in self.all_items():
            if item["id"] == key_text:
                return item

        # Then Houdini-style internal Name.
        for item in self.all_items():
            if item.get("name") == key_text:
                return item

        # Backward compatibility: visible Label can still resolve.
        for item in self.all_items():
            if item.get("label") == key_text:
                return item

        return None

    def get_value(
        self,
        key,
        default=None
    ):
        item = self.find_item(
            key
        )

        if item is None:
            return default

        if "value" not in item:
            return default

        return copy.deepcopy(
            item["value"]
        )

    # ------------------------------------------------------------------
    # Field API
    # ------------------------------------------------------------------

    def register_field_widget(
        self,
        item_id,
        widget
    ):
        self.field_widgets[
            text_type(item_id)
        ] = widget

    def field_display_text(
        self,
        key
    ):
        item = self.find_item(
            key
        )

        if (
            item is None or
            item.get("kind") != "field"
        ):
            return ""

        value = item.get(
            "value",
            ""
        )

        if value is None:
            return ""

        if isinstance(
            value,
            (list, tuple)
        ):
            return ", ".join(
                text_type(entry)
                for entry in value
            )

        return text_type(
            value
        )

    def refresh_field_widget(
        self,
        key
    ):
        item = self.find_item(
            key
        )

        if item is None:
            return

        widget = self.field_widgets.get(
            item["id"]
        )

        if widget is not None:
            try:
                widget.refresh()
            except Exception:
                pass

    def field_scene_objects(
        self,
        key
    ):
        item = self.find_item(
            key
        )

        if (
            item is None or
            item.get("kind") != "field"
        ):
            return []

        value = item.get(
            "value",
            ""
        )

        if isinstance(
            value,
            (list, tuple)
        ):
            candidates = [
                text_type(entry)
                for entry in value
            ]
        else:
            value = text_type(
                value or ""
            )

            # Prefer an exact scene object match.
            if value and cmds.objExists(
                value
            ):
                candidates = [
                    value
                ]
            else:
                normalized = (
                    value
                    .replace(";", "\\n")
                    .replace(",", "\\n")
                )

                candidates = [
                    part.strip()
                    for part in normalized.splitlines()
                    if part.strip()
                ]

        return [
            candidate
            for candidate in candidates
            if cmds.objExists(
                candidate
            )
        ]

    def select_field_objects(
        self,
        key
    ):
        objects = self.field_scene_objects(
            key
        )

        if not objects:
            return False

        try:
            cmds.select(
                objects,
                replace=True
            )
            return True
        except Exception:
            return False

    def refresh_selection_fields(
        self,
        force=False
    ):
        selection_fields = [
            item
            for item in self.all_items()
            if (
                item.get("kind") == "field" and
                item.get("source") == "selection"
            )
        ]

        if not selection_fields:
            return

        try:
            raw_selection = cmds.ls(
                selection=True,
                long=True
            ) or []
        except Exception:
            raw_selection = []

        signature = tuple(
            raw_selection
        )

        if (
            not force and
            signature == self._selection_signature
        ):
            return

        self._selection_signature = signature

        for item in selection_fields:
            try:
                if item.get(
                    "long_names",
                    False
                ):
                    values = list(
                        raw_selection
                    )
                else:
                    values = cmds.ls(
                        raw_selection,
                        long=False
                    ) or []

                if not item.get(
                    "multiple",
                    True
                ):
                    values = values[:1]

                item["value"] = values

                self.refresh_field_widget(
                    item["id"]
                )

            except Exception:
                pass

    def set_result(
        self,
        key,
        value
    ):
        """
        Convenience alias intended for Button scripts.

        Example:
            toolbox.set_result(
                "selected_object",
                cmds.ls(sl=True)
            )
        """
        return self.set_value(
            key,
            value
        )

    def normalize_value_for_item(
        self,
        item,
        value
    ):
        kind = item.get("kind")

        if kind == "field":
            if value is None:
                return ""

            if isinstance(
                value,
                (list, tuple)
            ):
                return [
                    text_type(entry)
                    for entry in value
                ]

            return text_type(
                value
            )

        if kind == "string":
            return text_type(
                value
            )

        if kind == "integer":
            return _clamp(
                _safe_int(
                    value,
                    item["value"]
                ),
                item["min"],
                item["max"]
            )

        if kind == "float":
            return _clamp(
                _safe_float(
                    value,
                    item["value"]
                ),
                item["min"],
                item["max"]
            )

        if kind in (
            "toggle",
            "checkbox"
        ):
            return bool(
                value
            )

        if kind == "menu":
            value = text_type(
                value
            )
            if value in item["items"]:
                return value

            return item["items"][0]

        if kind == "color":
            return _safe_color(
                value
            )

        return value

    def store_value(
        self,
        key,
        value
    ):
        item = self.find_item(
            key
        )

        if item is None:
            return False

        if "value" not in item:
            return False

        item["value"] = self.normalize_value_for_item(
            item,
            value
        )

        self.save()
        return True

    def set_value(
        self,
        key,
        value
    ):
        item = self.find_item(
            key
        )

        if not self.store_value(
            key,
            value
        ):
            return False

        if (
            item is not None and
            item.get("kind") == "field"
        ):
            self.refresh_field_widget(
                item["id"]
            )
            return True

        self.rebuild()
        return True

    # ------------------------------------------------------------------
    # Runtime interface
    # ------------------------------------------------------------------

    def rebuild(self):
        self.field_widgets = {}

        while (
            self.content_layout.count() >
            1
        ):
            item = self.content_layout.takeAt(
                0
            )

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        folders = self.config["sections"]
        index = 0

        while index < len(
            folders
        ):
            folder = folders[
                index
            ]

            folder_type = folder.get(
                "folder_type",
                "collapsible"
            )

            if folder_type in (
                "tabs",
                "radio"
            ):
                group = [
                    folder
                ]
                index += 1

                while index < len(
                    folders
                ):
                    candidate = folders[
                        index
                    ]

                    if candidate.get(
                        "folder_type",
                        "collapsible"
                    ) != folder_type:
                        break

                    group.append(
                        candidate
                    )
                    index += 1

                if folder_type == "tabs":
                    widget = RuntimeFolderTabs(
                        self,
                        group,
                        self.content
                    )
                else:
                    widget = RuntimeFolderRadio(
                        self,
                        group,
                        self.content
                    )

            else:
                widget = RuntimeSection(
                    self,
                    folder,
                    self.content
                )
                index += 1

            self.content_layout.insertWidget(
                self.content_layout.count() - 1,
                widget
            )

        self.refresh_selection_fields(
            force=True
        )

    def run_item(
        self,
        item_id
    ):
        item = self.find_item(
            item_id
        )

        if (
            not item or
            item.get("kind") != "button"
        ):
            return

        code = item.get(
            "click_script",
            ""
        )

        if (
            _shift_pressed() and
            item.get(
                "shift_script",
                ""
            ).strip()
        ):
            code = item.get(
                "shift_script",
                ""
            )

        success = execute_script(
            code,
            item.get(
                "language",
                "python"
            ),
            parent=self,
            toolbox=self
        )

        if success:
            self.statusBar().showMessage(
                "Executed: {0}".format(
                    item.get("label", item["name"])
                ),
                2500
            )

    # ------------------------------------------------------------------
    # Editor / reload
    # ------------------------------------------------------------------

    def open_interface_editor(self):
        try:
            if (
                self.editor_window is not None and
                self.editor_window.isVisible()
            ):
                self.editor_window.raise_()
                self.editor_window.activateWindow()
                return
        except Exception:
            pass

        self.editor_window = InterfaceEditor(
            self,
            parent=self
        )

        self.editor_window.show()
        self.editor_window.raise_()
        self.editor_window.activateWindow()

    def reload_config(self):
        self.config = load_config()
        self.rebuild()

        self.statusBar().showMessage(
            "Config reloaded.",
            2500
        )


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------

def show():
    global _TOOLBOX

    try:
        if _TOOLBOX is not None:
            _TOOLBOX.close()
            _TOOLBOX.deleteLater()
    except Exception:
        pass

    _TOOLBOX = ScriptToolbox(
        parent=maya_main_window()
    )

    _TOOLBOX.show()
    _TOOLBOX.raise_()
    _TOOLBOX.activateWindow()

    return _TOOLBOX