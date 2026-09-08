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

/* Runtime uses the same stable outer-panel contract as the first two panes in
   Interface Editor. RuntimePaneHost supplies the visible outside inset; the
   scroll area stays frameless and RuntimePane owns the actual outline. */
QWidget#RuntimePaneHost {
    background-color: #292929;
    border: 0px;
}

QFrame#RuntimePane {
    background-color: #303030;
    border: 1px solid #1b1b1b;
    border-radius: 3px;
}

QFrame#RuntimePane QScrollArea#ToolboxScroll {
    background-color: #2b2b2b;
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

/* Runtime Field lists are QAbstractScrollArea widgets. Maya/Qt4 paints their
   scrollbars inside the frame rect, so a border on the QListWidget itself can
   disappear behind the right/bottom scrollbar. ScrollSurfaceFrame owns the
   visible border; the list owns only its viewport/background. */
QListWidget#RuntimeFieldList {
    background-color: #202020;
    border: 0px;
    border-radius: 0px;
    padding: 1px;
}

QListWidget#RuntimeFieldList::item {
    min-height: 18px;
    padding: 1px 4px;
}

QListWidget#RuntimeFieldList::item:selected {
    background-color: #3b4348;
    color: #eeeeee;
}

"""

__all__ = ["RUNTIME_OVERRIDES"]
