# ADR 0001: Public/private repository boundary

- Status: Accepted
- Date: 2026-10-17

## Context

The project needs unusually complete evidence while some inputs contain
identifiers, configuration secrets, or third-party files whose redistribution
rights are unclear.

## Decision

Use exactly two authoritative repositories. `ThePirateRay` is public and holds
all normal development work. `ThePirateRay-PrivateStash` holds sensitive raw
data and redistribution-restricted third-party material. Google Drive is used
only as a read-only acquisition source.

Public documents cite private evidence by content-derived artifact ID and
SHA-256 digest. Git LFS is mandatory for binary files in PrivateStash. If the
Git server cannot store and retrieve LFS objects, raw binary import stops rather
than falling back to ordinary Git blobs.

## Consequences

- A public clone is useful without access to private evidence.
- Authorized researchers can reproduce claims from exact private bytes.
- Cross-repository commits must be ordered: private evidence first, sanitized
  public analysis second.
- The two repositories must be validated separately.
