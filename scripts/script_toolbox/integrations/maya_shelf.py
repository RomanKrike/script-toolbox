# -*- coding: utf-8 -*-
from __future__ import print_function

import re


SHELF_DOC_TAG = "ScriptToolbox/launcher"
SHELF_COMMAND = "import script_toolbox; script_toolbox.show()"
_TOKENS = re.compile(
    r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|[{};()]|[^\s{};()"]+', re.S
)


def _value(token):
    if token.startswith('"') and token.endswith('"'):
        escapes = {'"': '"', '\\': '\\', 'n': '\n', 'r': '\r', 't': '\t'}
        return re.sub(r'\\(["\\nrt])', lambda match: escapes[match.group(1)], token[1:-1])
    return token


def resaved_shelf_buttons(content):
    """Recognize launcher-only shelves, including duplicates; never evaluate MEL."""
    tokens = [match.group(0) for match in _TOKENS.finditer(content)
              if not match.group(0).startswith(("//", "/*"))]
    if not any(tokens[i:i + 3] == ["global", "proc", "shelf_ScriptToolbox"]
               for i in range(len(tokens) - 2)):
        return None
    buttons = [i for i, token in enumerate(tokens) if token == "shelfButton"]
    if not buttons:
        return None
    remaining = []
    result = []
    cursor = 0
    for begin in buttons:
        if begin < cursor:
            return None
        try:
            end = tokens.index(";", begin)
        except ValueError:
            return None
        flags = _button_flags(tokens[begin + 1:end])
        if flags is None or not is_launcher_button(flags):
            return None
        result.append(flags)
        remaining.extend(tokens[cursor:begin])
        cursor = end + 1
    remaining.extend(tokens[cursor:])
    # Outside the button, permit only the procedure and Maya's empty string buffers.
    # Extra commands, controls or custom startup code keep the file user-owned.
    for token in remaining:
        if token in ("global", "proc", "shelf_ScriptToolbox", "string",
                     "(", ")", "{", "}", ";", "=", '""'):
            continue
        if not re.match(r"^\$gBuffStr\d*$", token):
            return None
    return result


def _button_flags(body):
    aliases = {"-l": "-label", "-ann": "-annotation", "-c": "-command",
               "-stp": "-sourceType", "-dtg": "-docTag", "-i1": "-image1",
               "-image": "-image1", "-i": "-image1",
               "-w": "-width", "-h": "-height"}
    flags = {}
    if any(token in ("-q", "-query", "-e", "-edit") for token in body):
        return None
    for i in range(len(body) - 1):
        if body[i] in ("-doubleClickCommand", "-dcc", "-dragCallback", "-dgc",
                       "-dropCallback", "-dpc", "-visibleChangeCommand", "-vcc",
                       "-menuItem", "-mi") and _value(body[i + 1]):
            return None
        flag = aliases.get(body[i], body[i])
        if flag in ("-label", "-annotation", "-command", "-sourceType", "-docTag", "-image1", "-width", "-height"):
            flags[flag] = _value(body[i + 1])
    return flags


def is_launcher_button(flags):
    """Match managed metadata and a known command, including old callable reprs."""
    identity = flags.get("-docTag") == SHELF_DOC_TAG or (
        flags.get("-label") in ("ScriptToolbox", "Script Toolbox") and
        flags.get("-annotation") == "Open Script Toolbox"
    )
    command = flags.get("-command", "")
    if callable(command):
        return bool(identity and
                    getattr(command, "__name__", "") == "_open_toolbox" and
                    getattr(command, "__module__", "") ==
                    "script_toolbox.integrations.maya_runtime")
    command = (command or "").strip()
    known_command = bool(
        re.match(r"^import\s+script_toolbox\s*;\s*script_toolbox\.show\(\)\s*;?$", command) or
        re.match(r'^python\(\s*"import script_toolbox; script_toolbox\.show\(\)"\s*\)\s*;?$', command) or
        re.match(r"^<function _open_toolbox at (?:0x)?[0-9a-fA-F]+>$", command)
    )
    return bool(identity and known_command)


def resaved_shelf_button(content):
    """Return representative metadata only when every saved button is ours."""
    buttons = resaved_shelf_buttons(content)
    return buttons[0] if buttons else None


def resaved_shelf_is_current(content, icon_path):
    buttons = resaved_shelf_buttons(content)
    if not buttons or len(buttons) != 1:
        return False
    flags = buttons[0]
    return bool(flags and
                flags.get("-docTag") == SHELF_DOC_TAG and
                flags.get("-sourceType") == "python" and
                flags.get("-command") == SHELF_COMMAND and
                flags.get("-width") == "34" and
                flags.get("-height") == "34" and
                flags.get("-image1", "").replace("\\", "/") == icon_path.replace("\\", "/"))
