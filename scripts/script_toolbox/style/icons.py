# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore
from ..compat import QtGui

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


def toolbar_icon(kind, size=18):
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

    return QtGui.QIcon(pixmap)


__all__ = ["toolbar_icon"]
