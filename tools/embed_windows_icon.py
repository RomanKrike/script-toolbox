# -*- coding: utf-8 -*-
from __future__ import print_function

import argparse
import ctypes
import os
import struct
import sys

from ctypes import wintypes


RT_ICON = 3
RT_GROUP_ICON = 14
LANG_NEUTRAL = 0


class IconResourceError(RuntimeError):
    pass


def parse_ico(path):
    with open(path, "rb") as handle:
        data = handle.read()

    if len(data) < 6:
        raise IconResourceError(
            "ICO file is too small: {0}".format(path)
        )

    reserved, icon_type, count = struct.unpack_from(
        "<HHH",
        data,
        0
    )

    if reserved != 0 or icon_type != 1 or count <= 0:
        raise IconResourceError(
            "Invalid Windows ICO header: {0}".format(path)
        )

    directory_size = 6 + (16 * count)
    if len(data) < directory_size:
        raise IconResourceError(
            "ICO directory is truncated: {0}".format(path)
        )

    entries = []
    for index in range(count):
        offset = 6 + (index * 16)
        (
            width,
            height,
            color_count,
            entry_reserved,
            planes,
            bit_count,
            byte_count,
            image_offset,
        ) = struct.unpack_from(
            "<BBBBHHII",
            data,
            offset
        )

        if entry_reserved != 0:
            raise IconResourceError(
                "ICO entry {0} has an invalid reserved field.".format(index)
            )

        image_end = image_offset + byte_count
        if (
            byte_count <= 0 or
            image_offset < directory_size or
            image_end > len(data)
        ):
            raise IconResourceError(
                "ICO entry {0} points outside the file.".format(index)
            )

        entries.append({
            "width": width,
            "height": height,
            "color_count": color_count,
            "planes": planes,
            "bit_count": bit_count,
            "data": data[image_offset:image_end],
        })

    return entries


def build_group_icon(entries):
    chunks = [
        struct.pack(
            "<HHH",
            0,
            1,
            len(entries)
        )
    ]

    for resource_id, entry in enumerate(entries, 1):
        chunks.append(
            struct.pack(
                "<BBBBHHIH",
                entry["width"],
                entry["height"],
                entry["color_count"],
                0,
                entry["planes"],
                entry["bit_count"],
                len(entry["data"]),
                resource_id
            )
        )

    return b"".join(
        chunks
    )


def _windows_api():
    if os.name != "nt":
        raise IconResourceError(
            "Windows icon embedding can only run on Windows."
        )

    kernel32 = ctypes.WinDLL(
        "kernel32",
        use_last_error=True
    )

    begin = kernel32.BeginUpdateResourceW
    begin.argtypes = [
        wintypes.LPCWSTR,
        wintypes.BOOL,
    ]
    begin.restype = wintypes.HANDLE

    update = kernel32.UpdateResourceW
    update.argtypes = [
        wintypes.HANDLE,
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.WORD,
        ctypes.c_void_p,
        wintypes.DWORD,
    ]
    update.restype = wintypes.BOOL

    end = kernel32.EndUpdateResourceW
    end.argtypes = [
        wintypes.HANDLE,
        wintypes.BOOL,
    ]
    end.restype = wintypes.BOOL

    load_library = kernel32.LoadLibraryExW
    load_library.argtypes = [
        wintypes.LPCWSTR,
        wintypes.HANDLE,
        wintypes.DWORD,
    ]
    load_library.restype = wintypes.HMODULE

    find_resource = kernel32.FindResourceW
    find_resource.argtypes = [
        wintypes.HMODULE,
        ctypes.c_void_p,
        ctypes.c_void_p,
    ]
    find_resource.restype = wintypes.HRSRC

    free_library = kernel32.FreeLibrary
    free_library.argtypes = [
        wintypes.HMODULE,
    ]
    free_library.restype = wintypes.BOOL

    return (
        begin,
        update,
        end,
        load_library,
        find_resource,
        free_library,
    )


def _raise_last_error(message):
    error = ctypes.get_last_error()
    raise IconResourceError(
        "{0}: {1}".format(
            message,
            ctypes.WinError(error)
        )
    )


def embed_icon(executable_path, icon_path):
    executable_path = os.path.abspath(
        executable_path
    )
    icon_path = os.path.abspath(
        icon_path
    )

    if not os.path.isfile(executable_path):
        raise IconResourceError(
            "Executable does not exist: {0}".format(executable_path)
        )
    if not os.path.isfile(icon_path):
        raise IconResourceError(
            "Icon does not exist: {0}".format(icon_path)
        )

    entries = parse_ico(
        icon_path
    )
    group_data = build_group_icon(
        entries
    )

    (
        begin,
        update,
        end,
        _load_library,
        _find_resource,
        _free_library,
    ) = _windows_api()

    handle = begin(
        executable_path,
        False
    )
    if not handle:
        _raise_last_error(
            "BeginUpdateResourceW failed"
        )

    committed = False
    try:
        for resource_id, entry in enumerate(entries, 1):
            payload = entry["data"]
            buffer = ctypes.create_string_buffer(
                payload
            )

            if not update(
                handle,
                ctypes.c_void_p(RT_ICON),
                ctypes.c_void_p(resource_id),
                LANG_NEUTRAL,
                ctypes.cast(
                    buffer,
                    ctypes.c_void_p
                ),
                len(payload)
            ):
                _raise_last_error(
                    "UpdateResourceW failed for icon image {0}".format(
                        resource_id
                    )
                )

        group_buffer = ctypes.create_string_buffer(
            group_data
        )

        if not update(
            handle,
            ctypes.c_void_p(RT_GROUP_ICON),
            ctypes.c_void_p(1),
            LANG_NEUTRAL,
            ctypes.cast(
                group_buffer,
                ctypes.c_void_p
            ),
            len(group_data)
        ):
            _raise_last_error(
                "UpdateResourceW failed for icon group"
            )

        if not end(
            handle,
            False
        ):
            _raise_last_error(
                "EndUpdateResourceW failed"
            )

        committed = True
    finally:
        if not committed:
            try:
                end(
                    handle,
                    True
                )
            except Exception:
                pass

    verify_icon_resource(
        executable_path
    )

    return True


def verify_icon_resource(executable_path):
    (
        _begin,
        _update,
        _end,
        load_library,
        find_resource,
        free_library,
    ) = _windows_api()

    LOAD_LIBRARY_AS_DATAFILE = 0x00000002
    LOAD_LIBRARY_AS_IMAGE_RESOURCE = 0x00000020

    module = load_library(
        os.path.abspath(executable_path),
        None,
        (
            LOAD_LIBRARY_AS_DATAFILE |
            LOAD_LIBRARY_AS_IMAGE_RESOURCE
        )
    )

    if not module:
        _raise_last_error(
            "LoadLibraryExW failed while verifying icon"
        )

    try:
        resource = find_resource(
            module,
            ctypes.c_void_p(1),
            ctypes.c_void_p(RT_GROUP_ICON)
        )
        if not resource:
            _raise_last_error(
                "Embedded application icon resource was not found"
            )
    finally:
        free_library(
            module
        )

    return True


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Embed a Windows ICO into an existing PE executable using the "
            "Win32 resource update API."
        )
    )
    parser.add_argument(
        "--exe",
        required=True
    )
    parser.add_argument(
        "--icon",
        required=True
    )

    args = parser.parse_args(
        argv
    )

    embed_icon(
        args.exe,
        args.icon
    )

    print(
        "Embedded application icon into {0}".format(
            args.exe
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )
