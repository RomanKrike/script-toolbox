# -*- coding: utf-8 -*-

# Runtime-only QSS fixes that must override the base theme. Keeping these
# rules separate makes host-specific Qt4/Qt5 rendering quirks explicit.
RUNTIME_OVERRIDES = """
/* Qt4/Qt5 can mis-size the first tooltip when QToolTip uses QSS padding.
   The next tooltip is then laid out correctly, which looks like the first
   line was clipped until the cursor moves to another control. Keep tooltip
   colors/border from the base theme, but let the native style own its text
   margins so geometry is stable in Maya 2015 and newer hosts. */
QToolTip {
    padding: 0px;
}

/* Keep Parameter Description on the same surface as the main dialog. The
   base theme historically used #303030 here, which reads as a light slab
   against the #292929 editor window. Explicit palette fallbacks are installed
   separately for Maya 2015 / Qt4, where viewport QSS is not reliable. */
QWidget#PropertyPane,
QScrollArea#PropertyScroll,
QWidget#PropertyViewport,
QWidget#PropertyHost,
QWidget#PropertyEditor {
    background-color: #292929;
    border: 0px;
}

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

/* Runtime Field list uses the same inner surface language as the parameter
   trees in the Interface Editor. The visible outer pane border is owned by
   ScrollSurfaceFrame so Maya/Qt4 scrollbars cannot cover its bottom/right
   edge. */
QListWidget#RuntimeFieldList {
    background-color: #242424;
    color: #d4d4d4;
    border: 0px;
    border-radius: 0px;
    outline: 0px;
    padding: 0px;
}

QListWidget#RuntimeFieldList::item {
    min-height: 20px;
    padding: 3px 4px;
    border: 0px;
}

QListWidget#RuntimeFieldList::item:hover {
    background-color: #333333;
}

QListWidget#RuntimeFieldList::item:selected {
    background-color: #68462c;
    color: #ffffff;
}

"""

__all__ = ["RUNTIME_OVERRIDES"]
