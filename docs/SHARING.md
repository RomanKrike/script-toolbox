# Encrypted sharing

Script Toolbox can share either the complete staged toolbox configuration or a
single parameter/subtree from the Interface Editor.

## Interface Editor

The two share actions beside Import / Export are:

- **Paste Shared** — reads an `STB1` share code from the system clipboard,
  downloads and decrypts the payload, then offers the normal Replace / Append /
  Insert-into-Folder modes for complete toolbox shares.
- **Share** — serializes the complete staged toolbox, compresses and encrypts it,
  uploads the ciphertext, and copies the resulting `STB1` share code to the
  system clipboard.

The Existing Parameters context menu also contains:

- **Share** — shares the selected parameter. Folder and layout containers include
  their complete subtree.
- **Paste Shared** — inserts a shared parameter using the same clone path as the
  editor clipboard, so imported IDs and conflicting technical names are
  regenerated and managed internal references are remapped.

Changes pasted into the Interface Editor remain staged until **Apply** or
**Accept**, and participate in the editor command history.

## Share code

Protocol version 1 uses this external form:

```text
STB1:<provider>:<paste-id>:<decryption-key>
```

The decryption key is intentionally part of the share code and is never uploaded
to the paste provider. Treat the complete `STB1` value as a secret bearer token:
anyone who receives it can download and decrypt that share while the provider
still retains the encrypted paste.

## Payload pipeline

The payload is processed as:

```text
Script Toolbox payload
  -> compact UTF-8 JSON
  -> zlib compression
  -> ChaCha20-Poly1305 authenticated encryption (RFC 8439)
  -> URL-safe base64
  -> ShareProvider upload
```

ChaCha20-Poly1305 provides confidentiality and authentication. Modified or
corrupted ciphertext is rejected before JSON is deserialized.

The protocol implementation has no third-party Python dependency so it remains
usable in the Maya 2015 / Python 2.7 compatibility target. CI verifies the
implementation against the RFC 8439 AEAD test vector and runs a dedicated
Python 2.7 encrypted-share smoke test.

## Provider abstraction

Network storage is isolated behind `ShareProvider`. New shares use automatic
provider selection. Script Toolbox first tries `PastesDevProvider` against the
public `pastes.dev` API and falls back to `DpasteProvider` if that request fails.
The selected provider is written into the `STB1` share code, so downloads always
return to the service that actually stored the encrypted payload.

Existing `STB1:dpaste:...` codes remain supported. Provider failover is only
needed while creating a share; reading a share uses the provider encoded in the
share code.

The provider receives only encrypted base64 text. The decryption key is never
sent to either public service. `pastes.dev` is used as the preferred provider;
its public API does not expose a per-paste expiry option. The dpaste fallback
retains the existing seven-day default expiry and one-request-per-second
throttling.

On Windows, a PowerShell TLS 1.2 fallback is available for old Python runtimes
that cannot negotiate a provider HTTPS connection directly. The fallback uses
terminating errors and dedicated request/response stream variables so a network
failure reports one useful error instead of cascading PowerShell null/stream
exceptions.

A different backend can be registered without changing the `STB1` codec:

```python
from script_toolbox.share import register_provider

register_provider(my_provider)
```

A provider implements:

```python
class MyProvider(ShareProvider):
    name = "my-provider"

    def upload(self, content, expiry_days=7):
        return paste_id

    def download(self, paste_id):
        return encrypted_content
```

Provider names and paste IDs are carried in the share code; the encrypted
payload format remains provider-independent.
