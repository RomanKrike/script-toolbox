# -*- coding: utf-8 -*-
from __future__ import print_function

import re

from ..constants import PLUGIN_VERSION
from ..hosts import HOST
from ..pycompat import text_type
from .codec import ShareCodecError
from .codec import decode_payload
from .codec import encode_payload
from .codec import make_payload
from .provider import DpasteProvider
from .provider import PastesDevProvider
from .provider import ShareProviderError


SHARE_PREFIX = "STB1"
_SHARE_PATTERN = re.compile(
    r"STB1:([A-Za-z0-9_-]+):([A-Za-z0-9_-]+):([A-Za-z0-9_-]+)"
)


class ShareError(RuntimeError):
    pass


DEFAULT_PROVIDER_NAMES = (
    "pastes-dev",
    "dpaste",
)

_PROVIDERS = {
    "pastes-dev": PastesDevProvider(),
    "dpaste": DpasteProvider(),
}


def register_provider(provider, replace=False):
    name = text_type(
        getattr(provider, "name", "") or ""
    ).strip().lower()

    if not name:
        raise ShareError(
            "Share provider must define a name."
        )

    if name in _PROVIDERS and not replace:
        raise ShareError(
            "Share provider already registered: {0}".format(name)
        )

    _PROVIDERS[name] = provider
    return provider


def get_provider(name):
    name = text_type(name or "").strip().lower()
    provider = _PROVIDERS.get(name)

    if provider is None:
        raise ShareError(
            "Unknown share provider: {0}".format(name)
        )

    return provider


def format_share_code(provider_name, paste_id, key_text):
    return "{0}:{1}:{2}:{3}".format(
        SHARE_PREFIX,
        text_type(provider_name).strip().lower(),
        text_type(paste_id).strip(),
        text_type(key_text).strip()
    )


def extract_share_code(value):
    value = text_type(value or "")
    match = _SHARE_PATTERN.search(value)

    if match is None:
        raise ShareError(
            "Clipboard does not contain an STB1 share code."
        )

    return match.group(0)


def parse_share_code(value):
    code = extract_share_code(value)
    match = _SHARE_PATTERN.match(code)

    return {
        "code": code,
        "provider": match.group(1).lower(),
        "paste_id": match.group(2),
        "key": match.group(3),
    }


def looks_like_share_code(value):
    try:
        extract_share_code(value)
        return True
    except Exception:
        return False


def _provider_candidates(provider_name):
    provider_name = text_type(
        provider_name or ""
    ).strip().lower()

    if provider_name and provider_name != "auto":
        return (provider_name,)

    return DEFAULT_PROVIDER_NAMES


def share_data(
    payload_type,
    data,
    provider_name="auto",
    expiry_days=7
):
    payload = make_payload(
        payload_type,
        data,
        plugin_version=PLUGIN_VERSION,
        host_key=HOST.key
    )

    try:
        blob_text, key_text = encode_payload(payload)
    except ShareCodecError as exc:
        raise ShareError(text_type(exc))
    except Exception as exc:
        raise ShareError(
            "Could not encrypt Script Toolbox share: {0}".format(
                exc
            )
        )

    failures = []

    for candidate_name in _provider_candidates(provider_name):
        try:
            provider = get_provider(candidate_name)
            paste_id = provider.upload(
                blob_text,
                expiry_days=expiry_days
            )
            return format_share_code(
                candidate_name,
                paste_id,
                key_text
            )
        except (
            ShareProviderError,
            ShareError
        ) as exc:
            failures.append(
                "{0}: {1}".format(
                    candidate_name,
                    text_type(exc)
                )
            )
        except Exception as exc:
            failures.append(
                "{0}: {1}".format(
                    candidate_name,
                    text_type(exc)
                )
            )

    raise ShareError(
        "All share providers failed. {0}".format(
            "; ".join(failures)
        )
    )


def fetch_shared_data(code):
    parsed = parse_share_code(code)

    try:
        provider = get_provider(
            parsed["provider"]
        )
        blob_text = provider.download(
            parsed["paste_id"]
        )
        payload = decode_payload(
            blob_text,
            parsed["key"]
        )
    except (
        ShareCodecError,
        ShareProviderError,
        ShareError
    ) as exc:
        raise ShareError(text_type(exc))
    except Exception as exc:
        raise ShareError(
            "Could not read Script Toolbox share: {0}".format(
                exc
            )
        )

    return payload


__all__ = [
    "DEFAULT_PROVIDER_NAMES",
    "SHARE_PREFIX",
    "ShareError",
    "extract_share_code",
    "fetch_shared_data",
    "format_share_code",
    "get_provider",
    "looks_like_share_code",
    "parse_share_code",
    "register_provider",
    "share_data",
]
