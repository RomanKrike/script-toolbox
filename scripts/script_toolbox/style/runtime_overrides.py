# -*- coding: utf-8 -*-

# Runtime-only QSS fixes that must override the base theme. Keeping these
# rules separate makes host-specific Qt4/Qt5 rendering quirks explicit.
RUNTIME_OVERRIDES = """
QFrame#RuntimeSeparatorLine {
    background-color: transparent;
    border: 0px;
    border-top: 1px solid #414346;
}

QFrame#RuntimeSeparatorLineVertical {
    background-color: transparent;
    border: 0px;
    border-left: 1px solid #414346;
}
"""

__all__ = ["RUNTIME_OVERRIDES"]
