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
        return re.sub(r'\\(["\\])', r'\1', token[1:-1])
    return token


def resaved_shelf_button(content):
    """Recognize a single saved launcher; never evaluate MEL or claim mixed shelves."""
    tokens = [match.group(0) for match in _TOKENS.finditer(content)
              if not match.group(0).startswith(("//", "/*"))]
    if not any(tokens[i:i + 3] == ["global", "proc", "shelf_ScriptToolbox"]
               for i in range(len(tokens) - 2)):
        return None
    buttons = [i for i, token in enumerate(tokens) if token == "shelfButton"]
    if len(buttons) != 1:
        return None
    begin = buttons[0]
    try:
        end = tokens.index(";", begin)
    except ValueError:
        return None
    # Outside the button, permit only the procedure and Maya's empty string buffers.
    # Extra commands, controls or custom startup code keep the file user-owned.
    for token in tokens[:begin] + tokens[end + 1:]:
        if token in ("global", "proc", "shelf_ScriptToolbox", "string",
                     "(", ")", "{", "}", ";", "=", '""'):
            continue
        if not re.match(r"^\$gBuffStr\d*$", token):
            return None
    aliases = {"-l": "-label", "-ann": "-annotation", "-c": "-command",
               "-stp": "-sourceType", "-dtg": "-docTag", "-i1": "-image1",
               "-image": "-image1", "-i": "-image1",
               "-w": "-width", "-h": "-height"}
    flags = {}
    body = tokens[begin + 1:end]
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
    identity = flags.get("-docTag") == SHELF_DOC_TAG or (
        flags.get("-label") in ("ScriptToolbox", "Script Toolbox") and
        flags.get("-annotation") == "Open Script Toolbox"
    )
    command = flags.get("-command", "").strip()
    known_command = bool(
        re.match(r"^import\s+script_toolbox\s*;\s*script_toolbox\.show\(\)\s*;?$", command) or
        re.match(r'^python\(\s*"import script_toolbox; script_toolbox\.show\(\)"\s*\)\s*;?$', command) or
        re.match(r"^<function _open_toolbox at (?:0x)?[0-9a-fA-F]+>$", command)
    )
    return flags if identity and known_command else None


def resaved_shelf_is_current(content, icon_path):
    flags = resaved_shelf_button(content)
    return bool(flags and
                flags.get("-docTag") == SHELF_DOC_TAG and
                flags.get("-sourceType") == "python" and
                flags.get("-command") == SHELF_COMMAND and
                flags.get("-width") == "34" and
                flags.get("-height") == "34" and
                flags.get("-image1", "").replace("\\", "/") == icon_path.replace("\\", "/"))
