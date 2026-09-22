# -*- coding: utf-8 -*-
from __future__ import print_function

import fnmatch
import re

from .pycompat import text_type


DEFAULT_LAYER = "other"
DEFAULT_PATTERN = "Mask_prop_*"
DEFAULT_OUTPUT_DIR = (
    "[python {nuke.script_directory()}]"
    "../../../../out/v001/tzypa"
)
DEFAULT_FILENAME = "{channel}.png"
DEFAULT_SPACING = 180


def _patterns(value):
    value = text_type(value or "")
    return tuple(
        part.strip()
        for part in re.split(r"[,;\\n]+", value)
        if part.strip()
    )


def _natural_key(value):
    result = []
    for part in re.split(r"(\\d+)", text_type(value)):
        if part.isdigit():
            result.append((0, int(part)))
        else:
            result.append((1, part.lower()))
    return result


def find_channels(node, layer=DEFAULT_LAYER, pattern=DEFAULT_PATTERN):
    layer = text_type(layer or "").strip().rstrip(".")
    if not layer:
        return []

    prefix = layer + "."
    patterns = _patterns(pattern) or ("*",)
    result = set()

    for channel in node.channels():
        full_name = text_type(channel)
        if not full_name.startswith(prefix):
            continue

        short_name = full_name[len(prefix):]
        if any(fnmatch.fnmatchcase(short_name, item) for item in patterns):
            result.add(full_name)

    return sorted(
        result,
        key=lambda item: _natural_key(item[len(prefix):])
    )


def _set(node, knob_name, value):
    knob = node.knob(knob_name)
    if knob is not None:
        knob.setValue(value)


def _filename(channel, layer, template):
    prefix = text_type(layer).rstrip(".") + "."
    short_name = channel[len(prefix):] if channel.startswith(prefix) else channel
    short_name = re.sub(r'[<>:"/\\\\|?*]+', "_", short_name).strip(" .")

    try:
        name = text_type(template or DEFAULT_FILENAME).format(
            channel=short_name,
            layer=layer,
        )
    except Exception:
        name = short_name + ".png"

    if "." not in name.rsplit("/", 1)[-1]:
        name += ".png"
    return name


def build_mask_tree(
    source,
    layer=DEFAULT_LAYER,
    pattern=DEFAULT_PATTERN,
    output_dir=DEFAULT_OUTPUT_DIR,
    filename_template=DEFAULT_FILENAME,
    spacing=DEFAULT_SPACING,
):
    import nuke

    channels = find_channels(source, layer=layer, pattern=pattern)
    if not channels:
        return []

    try:
        spacing = max(120, int(spacing))
    except Exception:
        spacing = DEFAULT_SPACING

    undo = nuke.Undo()
    undo.begin("Build Mask Export Tree")
    created = []

    try:
        dot = nuke.nodes.Dot()
        dot.setInput(0, source)
        dot.setXYpos(
            source.xpos() + int(source.screenWidth() * 0.5) - 6,
            source.ypos() + source.screenHeight() + 80,
        )
        created.append(dot)

        start_x = int(
            dot.xpos()
            - ((len(channels) - 1) * spacing) * 0.5
            - 34
        )
        copy_y = dot.ypos() + 85

        for index, channel in enumerate(channels):
            x = start_x + index * spacing
            short_name = channel.split(".", 1)[1]

            copy_node = nuke.nodes.Copy()
            copy_node.setInput(0, dot)
            copy_node.setInput(1, dot)
            _set(copy_node, "from0", channel)
            _set(copy_node, "to0", "rgba.alpha")
            _set(copy_node, "label", short_name)
            copy_node.setXYpos(x, copy_y)

            shuffle = nuke.nodes.Shuffle()
            shuffle.setInput(0, copy_node)
            _set(shuffle, "red", "alpha")
            _set(shuffle, "green", "alpha")
            _set(shuffle, "blue", "alpha")
            _set(shuffle, "label", "[value in]")
            _set(shuffle, "note_font", "Verdana Bold")
            shuffle.setXYpos(x, copy_y + 55)

            unpremult = nuke.nodes.Unpremult()
            unpremult.setInput(0, shuffle)
            unpremult.setXYpos(x, copy_y + 133)

            write = nuke.nodes.Write()
            write.setInput(0, unpremult)
            _set(write, "channels", "rgba")
            _set(write, "file_type", "png")
            _set(write, "create_directories", True)
            _set(write, "checkHashOnRead", False)
            _set(write, "in_colorspace", "scene_linear")
            _set(write, "out_colorspace", "scene_linear")
            _set(write, "label", short_name)

            filename = _filename(channel, layer, filename_template)
            path = text_type(output_dir or "").rstrip("/\\")
            if path:
                path += "/"
            _set(write, "file", path + filename)
            write.setXYpos(x, copy_y + 272)

            created.extend((copy_node, shuffle, unpremult, write))
    finally:
        undo.end()

    return created


def build_from_selected(
    layer=DEFAULT_LAYER,
    pattern=DEFAULT_PATTERN,
    output_dir=DEFAULT_OUTPUT_DIR,
    filename_template=DEFAULT_FILENAME,
    spacing=DEFAULT_SPACING,
):
    import nuke

    selected = nuke.selectedNodes()
    if len(selected) != 1:
        nuke.message("Select exactly one source node.")
        return []

    created = build_mask_tree(
        selected[0],
        layer=layer,
        pattern=pattern,
        output_dir=output_dir,
        filename_template=filename_template,
        spacing=spacing,
    )

    if not created:
        nuke.message(
            "No channels matching {0}.{1} were found.".format(layer, pattern)
        )
    return created


__all__ = [
    "DEFAULT_FILENAME",
    "DEFAULT_LAYER",
    "DEFAULT_OUTPUT_DIR",
    "DEFAULT_PATTERN",
    "DEFAULT_SPACING",
    "build_from_selected",
    "build_mask_tree",
    "find_channels",
]
