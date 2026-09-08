# -*- coding: utf-8 -*-
from __future__ import print_function

import base64
import json
import zlib

from .crypto import CryptoError
from .crypto import decrypt
from .crypto import encrypt
from .crypto import random_key
from .crypto import random_nonce


FORMAT_NAME = "script-toolbox-share"
FORMAT_VERSION = 1
AAD = b"script-toolbox-share-v1"
MAX_ENCODED_BYTES = 2 * 1024 * 1024
MAX_JSON_BYTES = 10 * 1024 * 1024


class ShareCodecError(ValueError):
    pass


def _text_to_bytes(value):
    if isinstance(value, bytes):
        return value
    return value.encode("utf-8")


def _bytes_to_text(value):
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return value


def _b64encode(value):
    encoded = base64.urlsafe_b64encode(value)
    encoded = _bytes_to_text(encoded)
    return encoded.rstrip("=")


def _b64decode(value):
    value = value.strip()
    padding = "=" * ((4 - (len(value) % 4)) % 4)
    try:
        return base64.urlsafe_b64decode(
            _text_to_bytes(value + padding)
        )
    except Exception as exc:
        raise ShareCodecError(
            "Invalid base64 share payload: {0}".format(exc)
        )


def make_payload(
    payload_type,
    data,
    plugin_version="",
    host_key=""
):
    if payload_type not in ("config", "item"):
        raise ShareCodecError(
            "Unsupported share payload type: {0}".format(
                payload_type
            )
        )

    return {
        "format": FORMAT_NAME,
        "version": FORMAT_VERSION,
        "type": payload_type,
        "plugin_version": plugin_version or "",
        "host": host_key or "",
        "data": data,
    }


def validate_payload(payload):
    if not isinstance(payload, dict):
        raise ShareCodecError("Shared payload must be an object.")

    if payload.get("format") != FORMAT_NAME:
        raise ShareCodecError(
            "Clipboard data is not a Script Toolbox share."
        )

    if payload.get("version") != FORMAT_VERSION:
        raise ShareCodecError(
            "Unsupported Script Toolbox share version: {0}".format(
                payload.get("version")
            )
        )

    if payload.get("type") not in ("config", "item"):
        raise ShareCodecError(
            "Unsupported Script Toolbox share type."
        )

    if "data" not in payload:
        raise ShareCodecError(
            "Shared payload does not contain data."
        )

    return payload


def encode_payload(payload, key=None, nonce=None):
    validate_payload(payload)
    key = key or random_key()
    nonce = nonce or random_nonce()

    try:
        text = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True
        )
    except Exception as exc:
        raise ShareCodecError(
            "Could not serialize share payload: {0}".format(exc)
        )

    raw = _text_to_bytes(text)
    if len(raw) > MAX_JSON_BYTES:
        raise ShareCodecError(
            "Toolbox share is too large."
        )

    compressed = zlib.compress(raw, 9)

    try:
        ciphertext, tag = encrypt(
            key,
            nonce,
            compressed,
            aad=AAD
        )
    except CryptoError as exc:
        raise ShareCodecError(str(exc))

    blob = nonce + ciphertext + tag
    if len(blob) > MAX_ENCODED_BYTES:
        raise ShareCodecError(
            "Encrypted toolbox share is too large."
        )

    return _b64encode(blob), _b64encode(key)


def _safe_decompress(value):
    decompressor = zlib.decompressobj()
    try:
        raw = decompressor.decompress(
            value,
            MAX_JSON_BYTES + 1
        )
    except TypeError:
        # Compatibility for older zlib wrappers without max_length.
        raw = decompressor.decompress(value)
    except Exception as exc:
        raise ShareCodecError(
            "Could not decompress shared data: {0}".format(exc)
        )

    if (
        len(raw) > MAX_JSON_BYTES or
        getattr(decompressor, "unconsumed_tail", b"")
    ):
        raise ShareCodecError(
            "Decompressed toolbox share is too large."
        )

    try:
        raw += decompressor.flush()
    except Exception as exc:
        raise ShareCodecError(
            "Could not finish decompressing shared data: {0}".format(exc)
        )

    if len(raw) > MAX_JSON_BYTES:
        raise ShareCodecError(
            "Decompressed toolbox share is too large."
        )

    return raw


def decode_payload(blob_text, key_text):
    blob = _b64decode(blob_text)
    key = _b64decode(key_text)

    if len(blob) > MAX_ENCODED_BYTES:
        raise ShareCodecError(
            "Encrypted toolbox share is too large."
        )

    if len(blob) < 12 + 16:
        raise ShareCodecError(
            "Encrypted toolbox share is truncated."
        )

    nonce = blob[:12]
    ciphertext = blob[12:-16]
    tag = blob[-16:]

    try:
        compressed = decrypt(
            key,
            nonce,
            ciphertext,
            tag,
            aad=AAD
        )
    except CryptoError as exc:
        raise ShareCodecError(str(exc))

    raw = _safe_decompress(compressed)

    try:
        payload = json.loads(
            _bytes_to_text(raw)
        )
    except Exception as exc:
        raise ShareCodecError(
            "Could not read shared JSON: {0}".format(exc)
        )

    return validate_payload(payload)


__all__ = [
    "FORMAT_NAME",
    "FORMAT_VERSION",
    "ShareCodecError",
    "decode_payload",
    "encode_payload",
    "make_payload",
    "validate_payload",
]
