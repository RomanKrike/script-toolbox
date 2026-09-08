# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import struct
import sys


_AEAD_TAG_SIZE = 16
_KEY_SIZE = 32
_NONCE_SIZE = 12
_PY2 = sys.version_info[0] < 3


class CryptoError(ValueError):
    pass


def random_key():
    return os.urandom(_KEY_SIZE)


def random_nonce():
    return os.urandom(_NONCE_SIZE)


def _as_bytes(value):
    if isinstance(value, bytearray):
        return str(value) if _PY2 else bytes(value)
    if isinstance(value, bytes):
        return value
    try:
        return value.encode("utf-8")
    except Exception:
        raise CryptoError("Expected bytes-compatible value.")


def _rotl32(value, bits):
    return (
        ((value << bits) & 0xffffffff) |
        (value >> (32 - bits))
    )


def _quarter_round(state, a, b, c, d):
    state[a] = (state[a] + state[b]) & 0xffffffff
    state[d] ^= state[a]
    state[d] = _rotl32(state[d], 16)

    state[c] = (state[c] + state[d]) & 0xffffffff
    state[b] ^= state[c]
    state[b] = _rotl32(state[b], 12)

    state[a] = (state[a] + state[b]) & 0xffffffff
    state[d] ^= state[a]
    state[d] = _rotl32(state[d], 8)

    state[c] = (state[c] + state[d]) & 0xffffffff
    state[b] ^= state[c]
    state[b] = _rotl32(state[b], 7)


def _chacha20_block(key, counter, nonce):
    key = _as_bytes(key)
    nonce = _as_bytes(nonce)

    if len(key) != _KEY_SIZE:
        raise CryptoError("ChaCha20 key must be 32 bytes.")
    if len(nonce) != _NONCE_SIZE:
        raise CryptoError("ChaCha20 nonce must be 12 bytes.")
    if counter < 0 or counter > 0xffffffff:
        raise CryptoError("ChaCha20 counter is out of range.")

    state = list(
        struct.unpack("<4I", b"expand 32-byte k") +
        struct.unpack("<8I", key) +
        (counter,) +
        struct.unpack("<3I", nonce)
    )
    working = list(state)

    for unused in range(10):
        _quarter_round(working, 0, 4, 8, 12)
        _quarter_round(working, 1, 5, 9, 13)
        _quarter_round(working, 2, 6, 10, 14)
        _quarter_round(working, 3, 7, 11, 15)

        _quarter_round(working, 0, 5, 10, 15)
        _quarter_round(working, 1, 6, 11, 12)
        _quarter_round(working, 2, 7, 8, 13)
        _quarter_round(working, 3, 4, 9, 14)

    result = [
        (working[index] + state[index]) & 0xffffffff
        for index in range(16)
    ]
    return struct.pack("<16I", *result)


def _chacha20_xor(key, nonce, counter, data):
    data = _as_bytes(data)
    output = bytearray()
    offset = 0

    while offset < len(data):
        if counter > 0xffffffff:
            raise CryptoError("ChaCha20 counter exhausted.")

        stream = _chacha20_block(
            key,
            counter,
            nonce
        )
        chunk = data[offset:offset + 64]
        chunk_values = bytearray(chunk)
        stream_values = bytearray(stream)

        output.extend(bytearray([
            chunk_values[index] ^ stream_values[index]
            for index in range(len(chunk_values))
        ]))

        offset += len(chunk)
        counter += 1

    return str(output) if _PY2 else bytes(output)


def _little_endian_to_int(value):
    result = 0
    for index, byte_value in enumerate(bytearray(value)):
        result |= int(byte_value) << (8 * index)
    return result


def _int_to_little_endian(value, length):
    result = bytearray([
        (value >> (8 * index)) & 0xff
        for index in range(length)
    ])
    return str(result) if _PY2 else bytes(result)


def _poly1305(message, key):
    message = _as_bytes(message)
    key = _as_bytes(key)

    if len(key) != 32:
        raise CryptoError("Poly1305 key must be 32 bytes.")

    r = _little_endian_to_int(key[:16])
    r &= 0x0ffffffc0ffffffc0ffffffc0fffffff
    s = _little_endian_to_int(key[16:])
    modulus = (1 << 130) - 5
    accumulator = 0

    for offset in range(0, len(message), 16):
        block = message[offset:offset + 16]
        number = (
            _little_endian_to_int(block) +
            (1 << (8 * len(block)))
        )
        accumulator = (
            (accumulator + number) * r
        ) % modulus

    tag = (
        accumulator + s
    ) & ((1 << 128) - 1)
    return _int_to_little_endian(tag, 16)


def _pad16(value):
    remainder = len(value) % 16
    if not remainder:
        return b""
    return b"\x00" * (16 - remainder)


def _mac_data(aad, ciphertext):
    return b"".join([
        aad,
        _pad16(aad),
        ciphertext,
        _pad16(ciphertext),
        struct.pack("<Q", len(aad)),
        struct.pack("<Q", len(ciphertext)),
    ])


def _constant_time_equal(left, right):
    left = _as_bytes(left)
    right = _as_bytes(right)

    if len(left) != len(right):
        return False

    difference = 0
    left_values = bytearray(left)
    right_values = bytearray(right)

    for index in range(len(left_values)):
        difference |= (
            left_values[index] ^
            right_values[index]
        )

    return difference == 0


def encrypt(key, nonce, plaintext, aad=b""):
    """Encrypt and authenticate bytes using RFC 8439 ChaCha20-Poly1305."""
    key = _as_bytes(key)
    nonce = _as_bytes(nonce)
    plaintext = _as_bytes(plaintext)
    aad = _as_bytes(aad)

    if len(key) != _KEY_SIZE:
        raise CryptoError("Encryption key must be 32 bytes.")
    if len(nonce) != _NONCE_SIZE:
        raise CryptoError("Encryption nonce must be 12 bytes.")

    one_time_key = _chacha20_block(
        key,
        0,
        nonce
    )[:32]
    ciphertext = _chacha20_xor(
        key,
        nonce,
        1,
        plaintext
    )
    tag = _poly1305(
        _mac_data(
            aad,
            ciphertext
        ),
        one_time_key
    )
    return ciphertext, tag


def decrypt(key, nonce, ciphertext, tag, aad=b""):
    """Authenticate and decrypt RFC 8439 ChaCha20-Poly1305 bytes."""
    key = _as_bytes(key)
    nonce = _as_bytes(nonce)
    ciphertext = _as_bytes(ciphertext)
    tag = _as_bytes(tag)
    aad = _as_bytes(aad)

    if len(key) != _KEY_SIZE:
        raise CryptoError("Encryption key must be 32 bytes.")
    if len(nonce) != _NONCE_SIZE:
        raise CryptoError("Encryption nonce must be 12 bytes.")
    if len(tag) != _AEAD_TAG_SIZE:
        raise CryptoError("Authentication tag must be 16 bytes.")

    one_time_key = _chacha20_block(
        key,
        0,
        nonce
    )[:32]
    expected_tag = _poly1305(
        _mac_data(
            aad,
            ciphertext
        ),
        one_time_key
    )

    if not _constant_time_equal(
        tag,
        expected_tag
    ):
        raise CryptoError(
            "Shared data failed authentication."
        )

    return _chacha20_xor(
        key,
        nonce,
        1,
        ciphertext
    )


__all__ = [
    "CryptoError",
    "decrypt",
    "encrypt",
    "random_key",
    "random_nonce",
]
