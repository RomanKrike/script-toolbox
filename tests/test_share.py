# -*- coding: utf-8 -*-

import copy

import pytest

from script_toolbox.share import service as service_module
from script_toolbox.share.codec import ShareCodecError
from script_toolbox.share.codec import decode_payload
from script_toolbox.share.codec import encode_payload
from script_toolbox.share.codec import make_payload
from script_toolbox.share.crypto import decrypt
from script_toolbox.share.crypto import encrypt
from script_toolbox.share.provider import ShareProvider
from script_toolbox.share.provider import ShareProviderError
from script_toolbox.share.service import fetch_shared_data
from script_toolbox.share.service import parse_share_code
from script_toolbox.share.service import register_provider
from script_toolbox.share.service import share_data


def _hex(value):
    return bytes.fromhex(
        "".join(value.split())
    )


def test_chacha20_poly1305_matches_rfc_8439_vector():
    key = _hex(
        "808182838485868788898a8b8c8d8e8f"
        "909192939495969798999a9b9c9d9e9f"
    )
    nonce = _hex("070000004041424344454647")
    aad = _hex("50515253c0c1c2c3c4c5c6c7")
    plaintext = _hex(
        "4c616469657320616e642047656e746c"
        "656d656e206f662074686520636c6173"
        "73206f66202739393a20496620492063"
        "6f756c64206f6666657220796f75206f"
        "6e6c79206f6e652074697020666f7220"
        "746865206675747572652c2073756e73"
        "637265656e20776f756c642062652069"
        "742e"
    )
    expected_ciphertext = _hex(
        "d31a8d34648e60db7b86afbc53ef7ec2"
        "a4aded51296e08fea9e2b5a736ee62d6"
        "3dbea45e8ca9671282fafb69da92728b"
        "1a71de0a9e060b2905d6a5b67ecd3b3"
        "692ddbd7f2d778b8c9803aee328091b5"
        "8fab324e4fad675945585808b4831d7bc"
        "3ff4def08e4b7a9de576d26586cec64b6"
        "116"
    )
    expected_tag = _hex("1ae10b594f09e26a7e902ecbd0600691")

    ciphertext, tag = encrypt(
        key,
        nonce,
        plaintext,
        aad=aad
    )

    assert ciphertext == expected_ciphertext
    assert tag == expected_tag
    assert decrypt(
        key,
        nonce,
        ciphertext,
        tag,
        aad=aad
    ) == plaintext


def test_payload_round_trip_and_tamper_detection():
    payload = make_payload(
        "item",
        {
            "kind": "string",
            "id": "item-a",
            "name": "asset_name",
            "label": "Asset Name",
            "value": "dragon",
        },
        plugin_version="1.2.3",
        host_key="maya"
    )
    blob, key = encode_payload(payload)

    assert decode_payload(blob, key) == payload

    index = len(blob) // 2
    replacement = "A" if blob[index] != "A" else "B"
    tampered = (
        blob[:index] +
        replacement +
        blob[index + 1:]
    )

    with pytest.raises(ShareCodecError):
        decode_payload(tampered, key)


class _MemoryProvider(ShareProvider):
    name = "memory-test"

    def __init__(self):
        self.values = {}
        self.counter = 0

    def upload(self, content, expiry_days=7):
        self.counter += 1
        paste_id = "P{0}".format(self.counter)
        self.values[paste_id] = content
        return paste_id

    def download(self, paste_id):
        return self.values[paste_id]


class _FailingProvider(ShareProvider):
    name = "failing-test"

    def upload(self, content, expiry_days=7):
        raise ShareProviderError("provider unavailable")

    def download(self, paste_id):
        raise ShareProviderError("provider unavailable")


def test_share_service_keeps_key_out_of_provider_payload():
    provider = _MemoryProvider()
    register_provider(
        provider,
        replace=True
    )
    data = {
        "kind": "button",
        "id": "button-a",
        "name": "publish",
        "label": "Publish",
        "click_script": "print('secret script')",
    }

    code = share_data(
        "item",
        copy.deepcopy(data),
        provider_name=provider.name
    )
    parsed = parse_share_code(code)
    stored = provider.values[
        parsed["paste_id"]
    ]

    assert code.startswith("STB1:memory-test:")
    assert parsed["key"] not in stored
    assert "secret script" not in stored

    payload = fetch_shared_data(code)
    assert payload["type"] == "item"
    assert payload["data"] == data


def test_share_service_falls_back_to_next_default_provider(monkeypatch):
    failing = _FailingProvider()
    memory = _MemoryProvider()
    memory.name = "working-test"

    monkeypatch.setattr(
        service_module,
        "_PROVIDERS",
        {
            failing.name: failing,
            memory.name: memory,
        }
    )
    monkeypatch.setattr(
        service_module,
        "DEFAULT_PROVIDER_NAMES",
        (
            failing.name,
            memory.name,
        )
    )

    code = share_data(
        "item",
        {
            "kind": "label",
            "id": "fallback-label",
            "name": "fallback_label",
            "label": "Fallback",
        }
    )
    parsed = parse_share_code(code)

    assert parsed["provider"] == memory.name
    assert parsed["paste_id"] in memory.values
