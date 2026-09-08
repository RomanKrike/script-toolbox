# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import sys


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)
SCRIPTS = os.path.join(ROOT, "scripts")

if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from script_toolbox.share.codec import decode_payload
from script_toolbox.share.codec import encode_payload
from script_toolbox.share.codec import make_payload
from script_toolbox.share.crypto import decrypt
from script_toolbox.share.crypto import encrypt


def from_hex(value):
    return "".join(value.split()).decode("hex")


def assert_rfc_vector():
    key = from_hex(
        "808182838485868788898a8b8c8d8e8f"
        "909192939495969798999a9b9c9d9e9f"
    )
    nonce = from_hex("070000004041424344454647")
    aad = from_hex("50515253c0c1c2c3c4c5c6c7")
    plaintext = from_hex(
        "4c616469657320616e642047656e746c"
        "656d656e206f662074686520636c6173"
        "73206f66202739393a20496620492063"
        "6f756c64206f6666657220796f75206f"
        "6e6c79206f6e652074697020666f7220"
        "746865206675747572652c2073756e73"
        "637265656e20776f756c642062652069"
        "742e"
    )
    expected_tag = from_hex(
        "1ae10b594f09e26a7e902ecbd0600691"
    )

    ciphertext, tag = encrypt(
        key,
        nonce,
        plaintext,
        aad=aad
    )

    if tag != expected_tag:
        raise AssertionError(
            "ChaCha20-Poly1305 RFC tag mismatch"
        )

    if decrypt(
        key,
        nonce,
        ciphertext,
        tag,
        aad=aad
    ) != plaintext:
        raise AssertionError(
            "ChaCha20-Poly1305 Python 2 round trip failed"
        )


def assert_codec_round_trip():
    payload = make_payload(
        "item",
        {
            "kind": "string",
            "id": "python2-share",
            "name": "asset_name",
            "label": u"Asset Name",
            "value": u"dragon",
        },
        plugin_version="python2-smoke",
        host_key="maya"
    )

    blob, key = encode_payload(payload)
    restored = decode_payload(blob, key)

    if restored != payload:
        raise AssertionError(
            "Encrypted share codec Python 2 round trip failed"
        )


if __name__ == "__main__":
    assert_rfc_vector()
    assert_codec_round_trip()
    print("Python 2 encrypted share smoke passed.")
